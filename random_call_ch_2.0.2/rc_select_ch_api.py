from rc_database_ch_api import *
from random import sample as random_sample


class UserInputException(Exception):
    def __init__(self, info):
        self.info = info

    def __str__(self):
        return self.info


def name_list_to_str(name: list) -> str:
    """
    convert a list to a visible str.
    :param name: a list to be dealt
    :return: a str that has been dealt
    """
    _result = ""
    for i in name:
        i += ","
        _result += i
    _result = _result.rstrip(",")
    return _result


def select_from_super_set(target: str, number: int = 1, return_type="str"):
    """
    target: to determine what sequence to select from.
    target should be one of '所有学生', '男生', '女生'.
    number: to determine how many objects to be selected.
    :return a str if return_type is 'str' , else, return a list
    """
    if target not in ['所有学生', '男生', '女生']:
        raise ValueError("var target should be one of '所有学生', '男生', '女生'")
    _dict_to_select = {'所有学生': SuperStudentSet.get_all, '男生': SuperStudentSet.get_male,
                       '女生': SuperStudentSet.get_female}
    _raw_list = _dict_to_select[target]()
    _raw_len = len(_raw_list)
    if number > _raw_len:
        raise UserInputException("请输入一个不大于 %s 的数字" % _raw_len)
    _result_list = random_sample(_raw_list, k=number)
    if return_type == "str":
        return name_list_to_str(_result_list)
    else:
        return _result_list


def select_from_groups_by_groupleaders(leaders: list, number: int = 1, return_type="str"):
    _raw_list = []
    if not leaders:
        raise UserInputException("请选择至少一个小组！")
    for i in leaders:
        a_target_list = StudentGroupSet.get_group_by_name(i)
        if not a_target_list:
            raise UserInputException(
                f"{i}组无效！\n"
                f"请遵循输入语法规则\n"
                f"语法详情请见帮助页面")
        _raw_list += a_target_list
    if len(_raw_list) < number:
        raise UserInputException(f'数字不能大于 {len(_raw_list)}')
    _result_list = random_sample(_raw_list, k=number)
    if return_type == "str":
        return name_list_to_str(_result_list)
    else:
        return _result_list


def select_a_certain_amount_of_groups(number: int = 1, return_type="str"):
    all_groups = StudentGroupSet.get_all_groupnames()
    if len(all_groups) < number:
        raise UserInputException(f'请输入一个不大于 {len(all_groups)} 的数字')
    _result_list = random_sample(all_groups, k=number)
    if return_type == "str":
        return name_list_to_str(_result_list)
    else:
        return _result_list
