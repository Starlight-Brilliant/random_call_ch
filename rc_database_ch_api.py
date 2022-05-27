from json import load as json_load
rc_source_path = r".\rc_source.json"
# C:\Users\Administrator\AppData\Local


class SuperStudentSet:
    with open(rc_source_path, 'r', encoding="utf-8") as _f:
        _cache = json_load(_f)
    _all = _cache["_all"]
    _female = _cache["_female"]
    _male = _cache["_male"]

    @classmethod
    def update(cls):
        with open(rc_source_path, 'r', encoding="utf-8") as _f:
            _cache = json_load(_f)
        cls._all = _cache["_all"]
        cls._female = _cache["_female"]
        cls._male = _cache["_male"]

    @classmethod
    def get_all(cls) -> list:
        return cls._all

    @classmethod
    def get_female(cls) -> list:
        return cls._female

    @classmethod
    def get_male(cls) -> list:
        return cls._male


class StudentGroupSet:
    with open(rc_source_path, 'r', encoding="utf-8") as _f:
        _cache = json_load(_f)
    _gall = _cache["_gall"]

    @classmethod
    def update(cls):
        with open(rc_source_path, 'r', encoding="utf-8") as _f:
            _cache = json_load(_f)
        cls._gall = _cache["_gall"]

    @classmethod
    def get_group_by_name(cls, name: str) -> list:
        for i1 in cls.__dict__.values():
            if isinstance(i1, dict):
                for i2 in i1.keys():
                    if i2 == name:
                        return i1[i2]

    @classmethod
    def get_groups_by_names(cls, names: list) -> list:
        _result = []
        for i in names:
            _result += StudentGroupSet.get_group_by_name(i)
        return _result

    @classmethod
    def get_all_groupnames(cls) -> list:
        result = []
        for i in cls._gall.keys():
            result.append(i)
        return result

    @classmethod
    def get_all_raw(cls) -> list:
        return cls._gall


