file_name_template = "{name:pascal}.cs"

default_type_template = "{type:pascal}"

types_map = {
    "bool": "bool",
    "str": "string",
    "list": "List<{type}>",
    "int": "int",
    "int64": "long",
    "float": "float"
}

class_template = """\
using System.Collections.Generic;
using Newtonsoft.Json;

namespace FlashcardsModern.WindowsUniversal.Model.Quizlet.Dto.Gen {{
    public class {name:pascal} {{\
    {body}\
    }}
}}
"""

field_template = """
        [JsonProperty("{name}")]
        public {type} {name:pascal} {{ get; set; }}
"""



