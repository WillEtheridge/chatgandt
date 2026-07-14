import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from chatgnt.records import ContractError
from chatgnt.validation import (
    FAILURE_LABELS,
    NORMATIVE_SCHEMA,
    RESPONSE_SCHEMA_PATH,
    canonical_validation_line,
    load_response_schema,
    load_response_schema_bytes,
    validate_response,
)


def ingredient(amount=1, unit="ml", name="idea"):
    return {"amount": amount, "unit": unit, "name": name}


def response(ingredient_count=3, method_count=2):
    return {
        "title": "The Confident Candidate",
        "ingredients": [
            ingredient(index + 1, "open-vocabulary scoops", f"idea {index}")
            for index in range(ingredient_count)
        ],
        "method": [f"Mix useful step {index}." for index in range(method_count)],
        "garnish": "One thoughtful question.",
    }


def raw(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class ValidationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_response_schema()

    def validate(self, value):
        return validate_response(value if isinstance(value, str) else raw(value), self.schema)

    def assert_labels(self, value, labels):
        result = self.validate(value)
        self.assertEqual(result["failure_labels"], labels)
        self.assertEqual(
            set(labels), {diagnostic["label"] for diagnostic in result["diagnostics"]}
        )
        return result


class ExactSchemaTests(ValidationTestCase):
    def test_schema_is_exact_and_passes_meta_schema(self):
        self.assertEqual(self.schema.value, NORMATIVE_SCHEMA)
        self.assertEqual(self.schema.raw_bytes, RESPONSE_SCHEMA_PATH.read_bytes())
        self.assertEqual(
            self.schema.sha256, hashlib.sha256(RESPONSE_SCHEMA_PATH.read_bytes()).hexdigest()
        )

    def test_same_id_schema_mutations_fail_before_validation(self):
        mutations = []
        added = copy.deepcopy(NORMATIVE_SCHEMA)
        added["description"] = "changed"
        mutations.append(added)
        removed = copy.deepcopy(NORMATIVE_SCHEMA)
        del removed["properties"]["title"]["pattern"]
        mutations.append(removed)
        changed = copy.deepcopy(NORMATIVE_SCHEMA)
        changed["properties"]["method"]["maxItems"] = 6
        mutations.append(changed)
        reordered = copy.deepcopy(NORMATIVE_SCHEMA)
        reordered["required"] = list(reversed(reordered["required"]))
        mutations.append(reordered)
        typed = copy.deepcopy(NORMATIVE_SCHEMA)
        typed["properties"]["ingredients"]["minItems"] = 3.0
        mutations.append(typed)
        for index, value in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(ContractError):
                    load_response_schema_bytes(raw(value).encode())

    def test_schema_loader_rejects_bad_encoding_bom_duplicates_and_bad_meta_schema(self):
        cases = [
            b"\xff",
            b"\xef\xbb\xbf" + RESPONSE_SCHEMA_PATH.read_bytes(),
            b'{"$id":"urn:chatgnt:schema:response:v1","$id":"duplicate"}',
            b'{"$schema":"https://json-schema.org/draft/2020-12/schema","type":7}',
        ]
        for value in cases:
            with self.subTest(value=value[:20]):
                with self.assertRaises(ContractError):
                    load_response_schema_bytes(value)

    def test_schema_object_order_and_formatting_are_irrelevant_but_bytes_are_hashed(self):
        reordered = {key: NORMATIVE_SCHEMA[key] for key in reversed(NORMATIVE_SCHEMA)}
        changed_bytes = json.dumps(reordered, indent=1).encode()
        loaded = load_response_schema_bytes(changed_bytes)
        self.assertEqual(loaded.value, NORMATIVE_SCHEMA)
        self.assertNotEqual(loaded.sha256, self.schema.sha256)
        first = validate_response(raw(response()), self.schema)
        second = validate_response(raw(response()), loaded)
        self.assertNotEqual(first["response_schema_sha256"], second["response_schema_sha256"])

    def test_path_loader_reports_missing_file_as_configuration_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ContractError):
                load_response_schema(Path(directory) / "missing.json")


class ValidResponseTests(ValidationTestCase):
    def test_behavioural_contract_example_passes(self):
        value = {
            "title": "The Confident Candidate",
            "ingredients": [
                ingredient(50, "ml", "role-specific preparation"),
                ingredient(25, "ml", "concrete examples"),
                ingredient(2, "dashes", "curiosity"),
            ],
            "method": [
                "Shake off generic preparation by researching the role, organisation, and interviewer.",
                "Stir together three STAR examples that demonstrate the skills the role requires.",
                "Strain each example down to the situation, your action, and a measurable result.",
                "Serve calmly, then finish with one thoughtful question about the team.",
            ],
            "garnish": "A clear understanding of why this particular role suits you.",
        }
        result = self.assert_labels(value, [])
        self.assertTrue(result["json_valid"])
        self.assertTrue(result["schema_valid"])

    def test_reordered_fields_and_json_whitespace_pass(self):
        value = response()
        reordered = {
            "method": value["method"],
            "garnish": value["garnish"],
            "title": value["title"],
            "ingredients": value["ingredients"],
        }
        result = self.assert_labels(" \t\r\n" + raw(reordered) + "\n\r\t ", [])
        self.assertEqual(
            result["observations"]["top_level_keys"],
            ["garnish", "ingredients", "method", "title"],
        )

    def test_inclusive_array_boundaries_and_number_forms_pass(self):
        for ingredient_count, method_count in ((3, 2), (8, 5)):
            value = response(ingredient_count, method_count)
            value["ingredients"][0]["amount"] = 3
            value["ingredients"][1]["amount"] = 0.125
            with self.subTest(ingredients=ingredient_count, methods=method_count):
                self.assertTrue(self.validate(value)["schema_valid"])

    def test_lossless_extreme_numbers_are_valid(self):
        prefix = (
            '{"title":"T","ingredients":['
            '{"amount":1,"unit":"u","name":"a"},'
            '{"amount":1e999999999999999999999999,"unit":"u","name":"b"},'
        )
        suffix = (
            ',"unit":"u","name":"c"}],"method":["a","b"],"garnish":"g"}'
        )
        huge = "1" + "0" * (max(sys.get_int_max_str_digits(), 4300) + 10)
        result = self.validate(prefix + '{"amount":' + huge + suffix)
        self.assertTrue(result["json_valid"])
        self.assertTrue(result["schema_valid"])


class ParserClassificationTests(ValidationTestCase):
    def test_markdown_fence_valid_duplicate_and_invalid_bodies(self):
        valid = "```json\n" + raw(response()) + "\n```"
        self.assert_labels(valid, ["markdown_fence"])
        duplicate = '```\n{"x":1,"x":2}\n```'
        result = self.assert_labels(duplicate, ["markdown_fence", "duplicate_key"])
        self.assertEqual(result["diagnostics"][1]["path"], "/x")
        for body in ("", "{", "{} {}", "before {} after"):
            with self.subTest(body=body):
                result = self.assert_labels(
                    "```json\n" + body + ("\n" if body else "") + "```",
                    ["markdown_fence", "json_syntax"],
                )
                self.assertNotIn("surrounding_text", result["failure_labels"])

    def test_exact_permitted_fence_grammar(self):
        object_text = raw(response())
        valid = [
            "```\n" + object_text + "\n```",
            "```json\n" + object_text + "\n```",
            "```  json-1.0_+\n" + object_text + "\n```  ",
            "``` json\r\n" + object_text + "\r\n```\t",
            " \r\n```\n" + object_text + "\n```\t\n ",
        ]
        for value in valid:
            with self.subTest(value=value[:20]):
                self.assertEqual(self.validate(value)["failure_labels"], ["markdown_fence"])

    def test_rejected_fence_forms_with_object_are_surrounding_text(self):
        object_text = raw(response())
        invalid = [
            "```json\r" + object_text + "\r```",
            "````json\n" + object_text + "\n````",
            "```json\n" + object_text + "\n ```",
            "```json extra\n" + object_text + "\n```",
            "```json\n" + object_text + "```",
            "```json\n" + object_text + "\n``` trailing",
        ]
        for value in invalid:
            with self.subTest(value=value[:30]):
                self.assertEqual(self.validate(value)["failure_labels"], ["surrounding_text"])

    def test_surrounding_prose_and_nested_canonical_object(self):
        object_text = raw(response())
        for value in ("before " + object_text, object_text + " after", "before " + object_text + " after"):
            with self.subTest(value=value[:20]):
                result = self.assert_labels(value, ["surrounding_text"])
                self.assertFalse(result["json_valid"])
                self.assertIsNone(result["observations"]["top_level_keys"])

    def test_malformed_outer_object_with_valid_nested_array_is_syntax(self):
        self.assert_labels('{"broken":[1,2]', ["json_syntax"])

    def test_duplicate_keys_at_root_and_nested_escaped_paths(self):
        root = self.assert_labels('{"a":1,"a":2}', ["duplicate_key"])
        self.assertEqual(root["diagnostics"][0]["path"], "/a")
        nested_raw = (
            '{"title":"T","ingredients":[{"amount":1,"unit":"u",'
            '"a/b~c":1,"a/b~c":2,"name":"n"},'
            '{"amount":1,"unit":"u","name":"n"},'
            '{"amount":1,"unit":"u","name":"n"}],'
            '"method":["a","b"],"garnish":"g"}'
        )
        nested = self.assert_labels(nested_raw, ["duplicate_key"])
        self.assertEqual(nested["diagnostics"][0]["path"], "/ingredients/0/a~1b~0c")

    def test_repeated_duplicate_occurrences_are_retained(self):
        result = self.assert_labels('{"x":1,"x":2,"x":3}', ["duplicate_key"])
        self.assertEqual(len(result["diagnostics"]), 2)
        self.assertEqual(result["diagnostics"][0], result["diagnostics"][1])

    def test_empty_malformed_invalid_constants_and_positions(self):
        cases = [
            (" \t\n", "Output does not contain a JSON value."),
            ("{", "JSON syntax error at character 1."),
            ("NaN", "JSON contains an invalid numeric constant."),
            ("Infinity", "JSON contains an invalid numeric constant."),
            ("-Infinity", "JSON contains an invalid numeric constant."),
            ("1 x", "JSON syntax error at character 2."),
        ]
        for value, detail in cases:
            with self.subTest(value=value):
                result = self.assert_labels(value, ["json_syntax"])
                self.assertEqual(result["diagnostics"][0]["detail"], detail)

    def test_multiple_values_precede_surrounding_discovery(self):
        for value in ("{} 1", "1 {}", "{} []", "true null"):
            with self.subTest(value=value):
                result = self.assert_labels(value, ["json_syntax"])
                self.assertEqual(
                    result["diagnostics"][0]["detail"],
                    "Output contains multiple complete JSON values.",
                )

    def test_multiple_values_retain_duplicate_diagnostics(self):
        result = self.assert_labels('{"x":1,"x":2} 3', ["duplicate_key", "json_syntax"])
        self.assertEqual([item["label"] for item in result["diagnostics"]], ["duplicate_key", "json_syntax"])

    def test_valid_nonobjects_are_json_valid_but_schema_invalid(self):
        cases = [
            ('"scalar"', "string", "wrong_top_level_type"),
            ("[]", "array", "wrong_top_level_type"),
            ("null", "null", "null_value"),
            ("true", "boolean", "wrong_top_level_type"),
            ("7", "number", "wrong_top_level_type"),
        ]
        for value, observed, label in cases:
            with self.subTest(value=value):
                result = self.assert_labels(value, [label])
                self.assertTrue(result["json_valid"])
                self.assertFalse(result["schema_valid"])
                self.assertIsNone(result["observations"]["top_level_keys"])
                if label == "wrong_top_level_type":
                    self.assertIn(f"observed {observed}.", result["diagnostics"][0]["detail"])


class SchemaFailureTests(ValidationTestCase):
    def test_missing_and_unexpected_fields_at_both_closed_levels(self):
        value = response()
        del value["title"]
        value["extra/root"] = 1
        del value["ingredients"][0]["name"]
        value["ingredients"][0]["extra~ingredient"] = 1
        result = self.assert_labels(value, ["missing_field", "unexpected_field"])
        self.assertEqual(
            [(item["label"], item["path"]) for item in result["diagnostics"]],
            [
                ("missing_field", "/ingredients/0/name"),
                ("missing_field", "/title"),
                ("unexpected_field", "/extra~1root"),
                ("unexpected_field", "/ingredients/0/extra~0ingredient"),
            ],
        )

    def test_wrong_response_array_item_ingredient_and_field_types(self):
        value = response()
        value["title"] = []
        value["method"][0] = 3
        value["ingredients"][0] = "not object"
        value["ingredients"][1]["unit"] = []
        result = self.assert_labels(value, ["wrong_field_type"])
        self.assertEqual(
            [(item["path"], item["detail"]) for item in result["diagnostics"]],
            [
                ("/ingredients/0", "Expected object; observed string."),
                ("/ingredients/1/unit", "Expected string; observed array."),
                ("/method/0", "Expected string; observed number."),
                ("/title", "Expected string; observed array."),
            ],
        )

    def test_count_failures_and_wrong_array_type_suppression(self):
        for field, low, high, label, expected in (
            ("ingredients", 2, 9, "ingredient_count", "Expected 3–8 items; observed {count}."),
            ("method", 1, 6, "method_count", "Expected 2–5 items; observed {count}."),
        ):
            for count in (low, high):
                value = response()
                value[field] = (
                    [ingredient() for _ in range(count)]
                    if field == "ingredients"
                    else ["step" for _ in range(count)]
                )
                with self.subTest(field=field, count=count):
                    result = self.assert_labels(value, [label])
                    self.assertEqual(result["diagnostics"][0]["detail"], expected.format(count=count))
        value = response()
        value["ingredients"] = "three"
        value["method"] = {}
        self.assert_labels(value, ["wrong_field_type"])

    def test_null_replaces_type_at_root_response_and_ingredient_paths(self):
        root = self.assert_labels("null", ["null_value"])
        self.assertEqual(root["diagnostics"], [{"label": "null_value", "path": "", "detail": "Null is not permitted."}])
        value = response()
        value["title"] = None
        value["ingredients"][0] = None
        value["ingredients"][1]["amount"] = None
        result = self.assert_labels(value, ["null_value"])
        self.assertEqual(
            [item["path"] for item in result["diagnostics"]],
            ["/ingredients/0", "/ingredients/1/amount", "/title"],
        )

    def test_blank_strings_at_every_governed_string_location(self):
        value = response()
        value["title"] = ""
        value["ingredients"][0]["unit"] = " \t\n"
        value["ingredients"][1]["name"] = "\r"
        value["method"][0] = " "
        value["garnish"] = "\t"
        result = self.assert_labels(value, ["blank_string"])
        self.assertEqual(
            [item["path"] for item in result["diagnostics"]],
            ["/garnish", "/ingredients/0/unit", "/ingredients/1/name", "/method/0", "/title"],
        )
        self.assertTrue(all(item["detail"] == "String must contain a non-whitespace character." for item in result["diagnostics"]))

    def test_nonpositive_boolean_and_numeric_string_amounts(self):
        value = response()
        value["ingredients"][0]["amount"] = 0
        value["ingredients"][1]["amount"] = -1e99
        result = self.assert_labels(value, ["non_positive_amount"])
        self.assertEqual([item["path"] for item in result["diagnostics"]], ["/ingredients/0/amount", "/ingredients/1/amount"])
        for amount in (True, "1"):
            value = response()
            value["ingredients"][0]["amount"] = amount
            with self.subTest(amount=amount):
                result = self.assert_labels(value, ["wrong_field_type"])
                self.assertNotIn("non_positive_amount", result["failure_labels"])

    def test_independent_failures_labels_order_and_diagnostic_templates(self):
        value = response(2, 1)
        del value["title"]
        value["extra"] = 1
        value["ingredients"][0]["amount"] = 0
        value["ingredients"][0]["unit"] = " "
        value["method"][0] = None
        result = self.assert_labels(
            value,
            [
                "missing_field",
                "unexpected_field",
                "ingredient_count",
                "method_count",
                "null_value",
                "blank_string",
                "non_positive_amount",
            ],
        )
        self.assertEqual(result["failure_labels"], [label for label in FAILURE_LABELS if label in result["failure_labels"]])
        self.assertEqual(len(result["diagnostics"]), 7)

    def test_nonobject_ingredient_does_not_infer_object_fields(self):
        value = response()
        value["ingredients"][0] = 7
        result = self.assert_labels(value, ["wrong_field_type"])
        self.assertEqual(len(result["diagnostics"]), 1)
        self.assertEqual(result["diagnostics"][0]["path"], "/ingredients/0")


class EvidenceAndSerializationTests(ValidationTestCase):
    def test_result_is_closed_deterministic_and_round_trips(self):
        first = self.validate(response())
        second = self.validate(response())
        self.assertEqual(first, second)
        self.assertEqual(canonical_validation_line(first), canonical_validation_line(second))
        self.assertEqual(
            set(first),
            {
                "record_schema_version",
                "validator_version",
                "response_schema_id",
                "response_schema_sha256",
                "raw_output_sha256",
                "json_valid",
                "schema_valid",
                "failure_labels",
                "diagnostics",
                "observations",
            },
        )
        self.assertEqual(
            set(first["observations"]),
            {"raw_character_count", "top_level_keys", "ingredient_count", "method_step_count"},
        )
        self.assertEqual(json.loads(canonical_validation_line(first)), first)

    def test_raw_change_changes_hash_and_character_count(self):
        first = self.validate(raw(response()))
        second = self.validate(raw(response()) + " ")
        self.assertNotEqual(first["raw_output_sha256"], second["raw_output_sha256"])
        self.assertEqual(second["observations"]["raw_character_count"], first["observations"]["raw_character_count"] + 1)

    def test_invalid_candidates_never_populate_observations_or_schema_validity(self):
        result = self.validate("before " + raw(response()))
        self.assertFalse(result["json_valid"])
        self.assertFalse(result["schema_valid"])
        self.assertEqual(
            result["observations"],
            {"raw_character_count": len("before " + raw(response())), "top_level_keys": None, "ingredient_count": None, "method_step_count": None},
        )

    def test_surrogate_unexpected_and_duplicate_keys_serialize_as_strict_utf8(self):
        unexpected_raw = raw(response())[:-1] + ',"\\ud800":1}'
        unexpected = self.validate(unexpected_raw)
        self.assertEqual(unexpected["failure_labels"], ["unexpected_field"])
        unexpected_line = canonical_validation_line(unexpected)
        unexpected_line.decode("utf-8", errors="strict")
        self.assertIn(b"\\ud800", unexpected_line)
        self.assertEqual(json.loads(unexpected_line), unexpected)

        duplicate_raw = '{"\\udfff":1,"\\udfff":2}'
        duplicate = self.validate(duplicate_raw)
        self.assertEqual(duplicate["failure_labels"], ["duplicate_key"])
        duplicate_line = canonical_validation_line(duplicate)
        duplicate_line.decode("utf-8", errors="strict")
        self.assertIn(b"\\udfff", duplicate_line)
        self.assertEqual(json.loads(duplicate_line), duplicate)

    def test_non_ascii_is_unescaped_and_line_is_compact_with_one_newline(self):
        value = response()
        value["Café 🍸"] = 1
        line = canonical_validation_line(self.validate(value))
        self.assertIn("Café 🍸".encode(), line)
        self.assertTrue(line.endswith(b"\n"))
        self.assertFalse(line.endswith(b"\n\n"))
        self.assertNotIn(b": ", line)


if __name__ == "__main__":
    unittest.main()
