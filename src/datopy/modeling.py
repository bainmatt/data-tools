"""
Tools for data modeling, validation, and raw data processing, including
auto-generated data models and a flexible framework for ETL workflows.
"""

import json
import pprint
import doctest
import pandas as pd
from jsonschema import validate
from pydantic import BaseModel, Field, PositiveInt, ValidationError
from typing import (
    Annotated, Any, Callable, Collection, Dict, Iterable, List,
    NamedTuple, TypeVar,
)
from typing import TYPE_CHECKING

# import datopy._settings
from datopy.workflow import doctest_function

# Custom types
# (recursively) nested dict with arbitrary depth and pre-defined node type
# TODO check this!
NestedDict = dict[str, "NestedDict" | List[str] | None]
GenericNestedDict = dict[object, object]

# Define TypeVars
# XXX remove unused
# for dictionary (key/value type)
# _KT = TypeVar('_KT')
# _VT = TypeVar('_VT')


# ----------------------------------------
# --- Data dictionary generation utils ---
# ----------------------------------------

def list_to_dict(obj: list[object] | tuple[object] | set[object],
                 max_items: int | None = None) -> dict[int, object]:
    """
    Provide a dictionary representation of a list or other non-dictionary
    or string-like iterable, using indices as keys.

    Parameters
    ----------
    obj : list
        A list to convert to a dictionary representation.
    max_items : int, default=None
        Option to impose a limit on the number of elements to iterate over.
        Intended use: constructing pattern-based data models from a sample.

    Returns
    -------
    res : dict
        The supplied list's dictionary representation.

    Examples
    --------
    >>> from datopy.modeling import list_to_dict

    >>> my_list = [1, 'two', [3], {'four': 5}]
    >>> list_to_dict(my_list)
    {1: 1, 2: 'two', 3: [3], 4: {'four': 5}}

    >>> my_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    >>> list_to_dict(my_list, max_items=5)
    {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}

    >>> my_dict = dict(a=1, b='two')
    >>> list_to_dict(my_dict)
    Not running conversion since obj is already a dictionary.
    {'a': 1, 'b': 'two'}
    """

    if isinstance(obj, dict):
        print("Not running conversion since obj",  # type: ignore [unreachable]
              "is already a dictionary.")
        return obj
    else:
        return {(key + 1): value for key, value in enumerate(obj)
                if (max_items is None) or (key < max_items)}


def compare_dict_keys(
    dict1: GenericNestedDict | object,
    dict2: GenericNestedDict | object
) -> GenericNestedDict | str | None:
    """
    Recursively compare two dictionaries and identify missing keys.

    Parameters
    ----------
    dict1 : dict
        The reference dictionary.
    dict2 : dict
        The comparison dictionary to be checked against `dict1`.

    Returns
    -------
    result : dict | List[str] | None
        The nested dictionary of fields missing from `dict2` relative `dict1`.

    Examples
    --------
    Setup

    >>> from datopy.modeling import compare_dict_keys
    >>> import copy
    >>> dict1 = {'a1': 1, 'a2': 'two', 'a3': [3],
    ...          'b1': {'b11': 1, 'b12': 'two', 'b13': [3]},
    ...          'c1': {'c11': {'c111': 1, 'c112': 'two', 'c113': [3]}}
    ... }

    >>> from datopy.modeling import compare_dict_keys

    Identical dictionaries

    >>> dict2 = copy.deepcopy(dict1)
    >>> compare_dict_keys(dict1, dict2)

    Missing nesting level 0 key

    >>> del dict2['a1']
    >>> compare_dict_keys(dict1, dict2)
    {'missing_keys': ['a1']}

    Missing nesting level 1 key

    >>> dict2 = copy.deepcopy(dict1)
    >>> del dict2['b1']['b12']
    >>> compare_dict_keys(dict1, dict2)
    {'nested_diff': {'b1': {'missing_keys': ['b12']}}}

    Missing nesting level 2 key

    >>> dict2 = copy.deepcopy(dict1)
    >>> del dict2['c1']['c11']['c113']
    >>> compare_dict_keys(dict1, dict2)
    {'nested_diff': {'c1': {'nested_diff': {'c11': {'missing_keys': ['c113']}}}}}
    """

    if isinstance(dict1, dict) and not isinstance(dict2, dict):
        return "missing nested dictionary"

    if not (isinstance(dict1, dict) and isinstance(dict2, dict)):
        return None

    missing_keys = set(dict1.keys()) - set(dict2.keys())
    shared_keys = set(dict1.keys()).intersection(set(dict2.keys()))

    # Initialize difference dictionary
    diff_dict: dict[object, object] = {}

    for key in shared_keys:
        nested_diff = compare_dict_keys(dict1[key], dict2[key])
        # Add any differences to the difference
        if nested_diff is not None:
            diff_dict[key] = nested_diff

    # Return result if no missing keys or no diffs in nested dicts found
    if missing_keys or diff_dict:
        result: dict[object, object] = {}
        if missing_keys:
            result['missing_keys'] = list(missing_keys)
        if diff_dict:
            result['nested_diff'] = diff_dict
        return result

    # Return None if no missing keys or differences found
    return None


def apply_recursive(func: Callable[..., Any],
                    obj) -> dict[str | int, Any] | Any:
    """
    Convert a nested data structure (with explicit or implied key/value
    pairs) into a tree-like dictionary, applying a given function to
    terminal values.

    Parameters
    ----------
    func : Callable[..., Any]
        _description_
    obj :
        _description_

    Returns
    -------
    dict:
        _description_

    Examples
    --------
    >>> from datopy.modeling import apply_recursive

    Define the data

    >>> nested_data =  {'type': 'album', 'url': 'link.com', 'audio_features': [
    ...     {'loudness': -11.4, 'duration_ms': 251},
    ...     {'loudness': -15.5, 'duration_ms': 284}]}
    >>> print(nested_data)
    {'type': 'album', 'url': 'link.com', 'audio_features': [{'loudness': -11.4, 'duration_ms': 251}, {'loudness': -15.5, 'duration_ms': 284}]}

    Convert to json-friendly representation

    >>> serialized = apply_recursive(str, nested_data)
    >>> print(serialized)
    {'type': 'album', 'url': 'link.com', 'audio_features': {1: {'loudness': '-11.4', 'duration_ms': '251'}, 2: {'loudness': '-15.5', 'duration_ms': '284'}}}

    Convert to field/type pairs

    >>> schema = apply_recursive(lambda x: type(x).__name__, nested_data)
    >>> print(schema)
    {'type': 'str', 'url': 'str', 'audio_features': {1: {'loudness': 'float', 'duration_ms': 'int'}, 2: {'loudness': 'float', 'duration_ms': 'int'}}}
    """
    # Handle dictionary-like objects
    if hasattr(obj, 'items'):
        return {key: apply_recursive(func, value)
                for key, value in obj.items()}

    # Handle list-like objects
    elif isinstance(obj, (list, tuple, set)):
        return {key: apply_recursive(func, value)
                for key, value in list_to_dict(obj, max_items=5).items()}

    # Handle base cases
    elif isinstance(obj, str):
        return func(obj)
    else:
        return func(obj)


def schema_jsonify(obj: GenericNestedDict) -> GenericNestedDict:
    r"""
    _summary_

    Parameters
    ----------
    schema : dict
        _description_

    Returns
    -------
    dict : _description_

    Examples
    --------
    >>> import pprint
    >>> from datopy.modeling import schema_jsonify

    >>> original_schema = {'name': 'str', 'quantity': 'int', 'features': {1: {'volume': 'str', 'duration': 'float'}, 2: {'volume': 'str', 'duration': 'float'}}, 'creator': {'person': {'name': 'str'}, 'company': {'name': 'str', 'location': 'str'}}}
    >>> schema = schema_jsonify(original_schema)
    >>> schema = {**{"title": "title", "description": "description"}, **schema}
    >>> pprint.pp(schema, compact=True, depth=3)
    {'title': 'title',
     'description': 'description',
     'type': 'object',
     'properties': {'name': {'type': 'string'},
                    'quantity': {'type': 'number'},
                    'features': {'type': 'array',
                                 'minItems': 1,
                                 'maxItems': 2,
                                 'uniqueItems': True,
                                 'items': {...}},
                    'creator': {'type': 'object',
                                'properties': {...},
                                'required': [...]}},
     'required': ['name', 'quantity', 'features', 'creator']}
    """
    schema: GenericNestedDict = {}
    is_dict = isinstance(obj, dict)

    # Case 1 (array-like)
    if obj and is_dict and isinstance(list(obj.keys())[0], int):
        field_len = list(obj.keys())[-1]
        schema = {
            "type": 'array',  # coerced to object; includes tuple/list
            "minItems": 1,
            "maxItems": field_len,
            "uniqueItems": True
        }
        # Recurse on first item, assuming homogeneity for simplicity
        schema["items"] = schema_jsonify(obj[1])    # type: ignore [arg-type]
        return schema

    # Case 2 (dictionary)
    elif obj and is_dict:
        schema["type"] = "object"
        schema["properties"] = {}
        # Require all by default to easily edit later
        schema["required"] = list(obj.keys())

        for key, val in obj.items():
            # Recurse on each value
            schema["properties"][key] = schema_jsonify(val)    # type: ignore [index, arg-type]
        return schema

    # Base cases (non-container types)
    # "str" -> "string"
    elif obj == "str":    # type: ignore [comparison-overlap]
        schema["type"] = "string"
        return schema

    # "int"/"float" -> "number"
    elif obj in ("int", "float"):    # type: ignore [comparison-overlap]
        schema["type"] = "number"
        return schema

    else:
        schema["type"] = "null"
        return schema


# --------------------------------------------
# --- Data processing base types and class ---
# --------------------------------------------

class CustomTypes:
    """
    Reusable custom field types.
    Whitespace around commas should be stripped before analysis.
    """
    CSVstr = Annotated[str, Field(pattern=r'^[a-z, ]+$',
                                  description="Custom lowercase comma-separated string type. Excludes num and special chars")]
    CSVnumstr = Annotated[str, Field(pattern=r'^[a-z0-9,.! ]+$',
                                     description="Allows numerics")]
    CSVnumsent = Annotated[str, Field(pattern=r'^[a-z0-9,.! ]+$')]


# TODO implement BaseProcessor

class BaseProcessor:
    """_summary_

    Parameters
    ----------
    model : BaseModel
        _description_
    query : NamedTuple
        _description_

    Methods
    -------
    retrieve()
        Retrieve data for the query from the API of the supplied model.
    process()
        Process (extract/clean) retrieved data.
    to_df()
        Convert to a dataframe.

    Attributes
    ----------

    """

    def __init__(self, model: BaseModel, query: NamedTuple):
        self.query = query
        self.model = model

    def retrieve(self):
        """
        Retrieve data for the query from the API of the supplied model.

        Raises
        ------
            NotImplementedError: _description_
        """
        ### Retrieval routine goes here

        ###
        raise NotImplementedError
        # include return here? self assignment?

    def process(self):
        """
        Process (extract/clean) retrieved data.

        Raises
        ------
            NotImplementedError: _description_
        """
        ### Processing routine goes here

        ###
        # TODO raise NotRetrieved error (try model.obj)
        raise NotImplementedError

    def _validate(self):
        """
        Validate the processed data against the supplied model.

        Raises
        ------
            ValidationError: _description_
        """
        model = self.model
        model
        # try:
        #     model(**self.data)
        # except ValidationError as e:
        #     pprint.pp(e.errors())
        print("Validated")
        return None

    def to_df(self):
        """
        Load the data into a dataframe for further processing or analysis.
        """
        # Validate before loading
        self._validate()

        df = pd.DataFrame([self.data])
        return df


if __name__ == "__main__":
    # Comment out (2) to run all tests in script; (1) to run specific tests
    doctest.testmod(verbose=True)
    # doctest_function(get_film_metadata, globs=globals())

    ## One-off tests

    # type checks that compiler does not see/understand (run mypy on module)
    if TYPE_CHECKING:
        # reveal_type((1, 'hello'))
        pass
