# noinspection SpellCheckingInspection
"""
Нужно доработать скрипт из первого задания. Вот что он должен уметь:

клонировать репозитории с Гитхаба;
# выдавать статистику самых частых слов по глаголам или существительным (в зависимости от параметра отчёта);
# выдавать статистику самых частых слов названия функций или локальных переменных внутри функций (в зависимости от параметра отчёта);
# выводить результат в консоль, json-файл или csv-файл (в зависимости от параметра отчёта);
# принимать все аргументы через консольный интерфейс.

 При доработке предусмотреть, что вскоре в программу понадобится добавлять:

# получение кода из других места, не только с Гитхаба;
# парсеры других ЯП, не только Python;
# сохранение в кучу разных форматов;
# более сложные типы отчётов (не только частота частей речи в различных местах кода).
"""


import ast
import os
import sys
import collections
import json
import csv
from pprint import pprint

from nltk import pos_tag


class FileCreatorMixin:
    source_link = None
    source_type = None

    def create_path(self):
        if self.source_type == 'Local':
            self.path = self.source_link
        elif self.source_type == 'Github':
            print('Downloading repository...')
            self.path = self.source_link
        # todo: create github downloader


class TreesCreatorMixin:
    path = None
    parser = None
    language = None

    def get_trees(self, path, with_filenames=False, with_file_content=False) -> list[collections.namedtuple]:
        trees = []
        filenames = self.find_filenames_in_path(path)
        Tree = collections.namedtuple('Tree', 'filename main_file_content tree')

        for filename in filenames:
            with open(filename, 'r', encoding='utf-8') as attempt_handler:
                main_file_content = attempt_handler.read()

            try:
                tree = self.parser(main_file_content)  # ast.parse if python
            except SyntaxError as e:
                print(e)
                tree = None

            if with_filenames and with_file_content:
                trees.append(Tree(filename, main_file_content, tree))
            elif with_filenames:
                trees.append(Tree(filename=filename, main_file_content=None, tree=tree))
            else:
                trees.append(Tree(filename=None, main_file_content=None, tree=tree))

        print('trees generated')
        return trees

    @staticmethod
    def find_filenames_in_path(path):
        filenames = []
        is_max_length = False
        for dirname, dirs, files in os.walk(path, topdown=True):
            if is_max_length:
                break
            for file in files:
                if file.endswith('.py'):
                    filenames.append(os.path.join(dirname, file))
                else:
                    continue
                if len(filenames) == 100:
                    is_max_length = True
                    break
        print('total %s files' % len(filenames))
        return filenames


class NamesFromTreesMixin:
    name_parameter = None
    get_trees = None

    @staticmethod
    def make_flat_list(_list):
        """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
        return sum([list(item) for item in _list], [])

    @staticmethod
    def get_all_names(tree):
        return [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]

    def get_names_from_trees(self, trees):
        if self.name_parameter == 'Func':
            funcs_raw = self.make_flat_list([self.get_names_from_tree(tree, 'Func') for tree in trees])
            funcs = [func for func in funcs_raw if not self.is_magic(func)]
            return funcs
        elif self.name_parameter == 'Var':
            return self.make_flat_list([self.get_names_from_tree(tree, 'Var') for tree in trees])

    def get_names_from_tree(self, tree, name):
        if name == 'Func':
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        elif name == 'Var':
            funcs_args = self.make_flat_list([node.args.args for node in ast.walk(tree)
                                              if isinstance(node, ast.FunctionDef)])
            return [arg.arg for arg in funcs_args]

    def get_all_words_in_path(self, path):
        trees = [tree.tree for tree in self.get_trees(path) if tree]
        function_names = [func for func in self.make_flat_list([self.get_all_names(tree) for tree in trees])
                          if not self.is_magic(func)]

        def split_snake_case_name_to_words(name):
            return [n for n in name.split('_') if n]

        return self.make_flat_list(
            [split_snake_case_name_to_words(function_name) for function_name in function_names])

    @staticmethod
    def is_magic(func_name):
        if func_name.startswith('__') and func_name.endswith('__'):
            return True
        return False


class NamesAnalizerMixin:
    word_parameter = None

    def is_specified_word_type(self, word):
        if not word:
            return False
        pos_info = pos_tag([word])
        first_word = 0
        tag = 1
        if self.word_parameter == 'Verb':
            return pos_info[first_word][tag] == 'VB'
        elif self.word_parameter == 'Noun':
            return pos_info[first_word][tag] == 'NN'

    def get_word_type_from_variable_name(self, function_name):
        return [word for word in function_name.split('_') if self.is_specified_word_type(word)]


class ReportMixin:
    get_top_word_types_in_path = None
    output_dict = None
    output = None

    def make_report(self):
        self.words = []
        self.words += self.get_top_word_types_in_path()
        self.output_dict[self.output]()

    def _stdout_report(self, ):
        print('total %s words, %s unique' % (len(self.words), len(set(self.words))))
        for word, occurence in self.words:
            pprint(f'{word:<8s}: {occurence}')

    def _json_report(self):
        with open('report.json', 'w') as fp:
            json.dump(self.words, fp)

    def _csv_report(self):
        with open('report.csv', 'w', newline='') as fp:
            writer = csv.writer(fp, delimiter=',')
            writer.writerows(self.words)


class StaticAnalizer(FileCreatorMixin, TreesCreatorMixin, NamesFromTreesMixin, NamesAnalizerMixin, ReportMixin):
    """
    def __init__(self, source_link, source_type='Local', word_parameter='Verb', name_parameter='Func',
                 output='stdout', language='Python', report_type='Frequency')
    """
    def __init__(self, source_link='.', source_type='Local', word_parameter='Verb', name_parameter='Func',
                 output='stdout', language='Python', report_type='Frequency'):
        self.source_link = source_link
        print(f'SL: {source_link}')
        self.source_type = source_type
        self.word_parameter = word_parameter
        self.name_parameter = name_parameter
        self.output = output
        self.language = language
        if language == 'Python':
            self.parser = ast.parse
        self.report_type = report_type
        self.words = []
        self.output_dict={'stdout': self._stdout_report,
                          'json': self._json_report,
                          'csv': self._csv_report}
        self.create_path()

    def get_top_word_types_in_path(self):
        trees = [tree.tree for tree in self.get_trees(self.path) if tree]  # TreesCreatorMixin
        _vars = self.get_names_from_trees(trees)  # NamesFromTreesMixin
        print('vars extracted')
        if self.report_type == 'Frequency':
            return self.create_frequency_report(_vars)

    def create_frequency_report(self, _vars, top_size=10):
        word_types = self.make_flat_list([self.get_word_type_from_variable_name(function_name) for function_name in _vars])
        return collections.Counter(word_types).most_common(top_size)


if __name__ == '__main__':
    project = 'django'
    path = os.path.join('.', project)
    """
        def __init__(self, source_link, source_type='Local', word_parameter='Verb', name_parameter='Func',
                     output='stdout', language='Python', report_type='Frequency')
        """

    attr_list = ['source_link', 'source_type', 'word_parameter', 'name_parameter', 'output', 'language', 'report_type']
    attr_dict = {}
    print('Leave blank to use default')
    for param, default in zip(attr_list, StaticAnalizer.__init__.__defaults__):
        i = input(f'{param} (default is {default}): ')
        if i:
            attr_dict[param] = i
    print(attr_dict)
    static_analizer = StaticAnalizer(**attr_dict)
    static_analizer.make_report()





