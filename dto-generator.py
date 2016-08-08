import json
import string
import inflection
import os
import dto_template
import functools
import shutil
import argparse
import sys


class Config:
    dto_rename_map = []
    dto_ignore_fields = []


class CaseFormatter(string.Formatter):
    def format_field(self, value, format_spec):
        if format_spec == "pascal":
            return inflection.camelize(value, True)
        elif format_spec == "camel":
            return inflection.camelize(value, False)
        else:
            return super().format_field(value, format_spec)


formatter = CaseFormatter()


class FieldDescription:
    def __init__(self, name, type_name, generic=None):
        self.name = name
        self.type_name = type_name
        self.generic = generic

    def __hash__(self, *args, **kwargs):
        return hash(str(self))

    def __str__(self, *args, **kwargs):
        return str(self.name) + "-" + str(self.type_name) + (
            str(self.generic) if self.generic is not None else "")

    def __eq__(self, other, *args, **kwargs):
        return hash(self) == hash(other)


class DtoDescription:
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def __hash__(self, *args, **kwargs):
        return hash(str(self))

    def __str__(self, *args, **kwargs):
        return str(self.name) + "-" + functools.reduce(lambda agr, field: agr + str(field) + "\n", self.fields, "")


def get_type_name(type_class):
    type_name = type_class.__name__
    return type_name


def update_dtos(known_dtos, new_dto):
    fields_set = set(new_dto.fields)
    for known_dto in known_dtos:
        known_fields_set = set(known_dto.fields)
        if known_dto.name is not None and known_dto.name == new_dto.name:
            if known_fields_set.issuperset(fields_set):
                if known_dto.name is None:
                    known_dto.name = new_dto.name
                return
            elif known_fields_set.issubset(fields_set):
                known_dto.fields = new_dto.fields
                if known_dto.name is None:
                    known_dto.name = new_dto.name
                return
            else:
                known_dto.fields = known_fields_set.union(fields_set)
                return
    known_dtos.add(new_dto)


def reduce_flatten_dto(dto, known_dto, config, suggested_name=None):
    if isinstance(dto, list):
        elements_type = None
        for item in dto:
            if isinstance(item, dict):
                new_dto = reduce_flatten_dto(item, known_dto, config, suggested_name)
                element_type = new_dto.name
            else:
                element_type = get_type_name(type(item))
            if element_type:
                if not elements_type:
                    elements_type = element_type
                elif elements_type != element_type:
                    elements_type = get_type_name(type(object))
        return elements_type
    elif isinstance(dto, dict):
        fields = []
        dto_name = suggested_name
        for key, value in dto.items():
            if value is not None:
                field = None
                if isinstance(value, dict):
                    element_name = key
                    # parse special attribute to get dto name
                    if all(d.name != element_name for d in known_dto):
                        new_dto = reduce_flatten_dto(value, known_dto, config, element_name)
                        element_name = new_dto.name
                    field = FieldDescription(key, element_name)
                elif isinstance(value, list):
                    element_name = inflection.singularize(key)
                    elements_type = reduce_flatten_dto(value, known_dto, config, element_name)
                    if not elements_type:
                        elements_type = inflection.singularize(key)
                    field = FieldDescription(key, get_type_name(type(value)), elements_type)
                else:
                    if key == "__name__":
                        dto_name = value
                    else:
                        field = FieldDescription(key, get_type_name(type(value)))
                if field is not None:
                    fields.append(field)
        new_dto = DtoDescription(dto_name, fields)
        update_dtos(known_dto, new_dto)
        return new_dto
    return known_dto


def rename_dto(dtos, dto_rename_map):
    for dto in dtos:
        if dto.name in dto_rename_map:
            dto.name = dto_rename_map[dto.name]
        for field in dto.fields:
            if field.type_name in dto_rename_map:
                field.type_name = dto_rename_map[field.type_name]
            if field.generic in dto_rename_map:
                field.generic = dto_rename_map[field.generic]


def remove_fields(dtos, ignored_fields):
    for dto in dtos:
        if dto.name in ignored_fields:
            ignored_field = ignored_fields[dto.name]
            field = next(field for field in dto.fields if field.name == ignored_field)
            dto.fields.remove(field)


def apply_config(dtos, config):
    remove_fields(dtos, config.dto_ignore_fields)
    rename_dto(dtos, config.dto_rename_map)


def generate_field(field):
    out_type = dto_template.types_map.get(field.type_name)
    if out_type is None:
        out_type = formatter.format(dto_template.default_type_template, type=field.type_name)
    if field.generic is not None:
        generic_out_type = dto_template.types_map.get(field.generic)
        if generic_out_type is None:
            generic_out_type = formatter.format(dto_template.default_type_template, type=field.generic)
        out_type = formatter.format(out_type, type=generic_out_type)
    return formatter.format(dto_template.field_template, name=field.name, type=out_type)


def generate_class(dto):
    body = []
    for field in sorted(dto.fields, key=lambda field: field.name):
        body.append(generate_field(field))
    return formatter.format(dto_template.class_template, body="".join(body), name=dto.name)


parser = argparse.ArgumentParser(description='Generate dto classes.')
parser.add_argument("-i", "--input", type=str, help='Input JSON file', default="input")
parser.add_argument("-o", "--output", type=str, required=True, help='Directory where classes will be generated')
args = parser.parse_args()

if not os.path.exists(args.input):
    print("Input folder doesn't exist")
    sys.exit(3)
config = Config()
config_path = os.path.join(args.input, "config")
if os.path.exists(config_path):
    g = {}
    with open(config_path, "r") as f:
        exec(f.read(), g)
    for name, value in g.items():
        setattr(config, name, value)
dtos = set()
for input_file in os.listdir(args.input):
    if input_file.endswith(".json"):
        with open(os.path.join(args.input, input_file)) as json_dto:
            data = json.load(json_dto)
        reduce_flatten_dto(data, dtos, config)
        print("Precessed " + input_file)
apply_config(dtos, config)
dir = args.output
if os.path.exists(dir):
    shutil.rmtree(dir)
os.makedirs(dir)
for dto in dtos:
    if dto.name is not None:
        path = os.path.join(dir, formatter.format(dto_template.file_name_template, name=dto.name))
        out_class = generate_class(dto)
        with open(path, mode="w") as file:
            file.write(out_class)
