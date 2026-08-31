#!/usr/bin/env python3
"""Build schema-validated text+image SFT records for Math Scene extraction.

Raw internet datasets are deliberately not converted automatically. The
primary target is the application's ProviderDocument contract, generated from
deterministic grade 1-9 templates and validated by the same Pydantic model used
at runtime.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
MASTER_BE = ROOT / "master_be"
sys.path.insert(0, str(MASTER_BE))

from app.services.math_lab.analyzer import ProviderDocument  # noqa: E402


PROMPT_PATH = ROOT / "training/math_lab/prompts/math_scene_analyzer_system.txt"
OUTPUT_ROOT = ROOT / "training/math_lab/data/generated"
FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
EVIDENCE = {"confidence": 1.0, "status": "explicit"}


def quantity(role: str, value: float, label: str, unit: str = "one") -> dict:
    return {"role": role, "value": value, "unit": unit, "label": label, "evidence": EVIDENCE}


def unknown(role: str, kind: str, label: str, unit: str | None = "one") -> dict:
    return {"role": role, "kind": kind, "unit": unit, "label": label}


def document(
    stem: str,
    grade: int,
    domain: str,
    problem_type: str,
    quantities: list[dict],
    unknowns: list[dict],
    question_format: str = "short_answer",
    entities: list[dict] | None = None,
    constraints: list[dict] | None = None,
    start_time: str | None = None,
    choices: list[str] | None = None,
    extracted_text: str | None = None,
    relationships: list[dict] | None = None,
) -> dict:
    payload = {
        "extracted_text": extracted_text or stem,
        "questions": [{
            "question_number": "1",
            "stem": stem,
            "question_format": question_format,
            "choices": choices or [],
            "subquestions": [],
            "grade": grade,
            "domain": domain,
            "problem_type": problem_type,
            "entities": entities or [],
            "quantities": quantities,
            "unknowns": unknowns,
            "relationships": relationships or [],
            "constraints": constraints or [],
            "start_time": start_time,
            "end_time": None,
            "confidence": 1.0,
            "requires_review": False,
            "review_notes": [],
        }],
        "confidence": 1.0,
        "requires_review": False,
    }
    return ProviderDocument.model_validate(payload).model_dump(mode="json")


def build_case(family: str, index: int, rng: random.Random, split: str) -> tuple[str, dict]:
    variant = {"train": 0, "validation": 1, "test": 2}[split]
    if family == "work_rate_with_variable_people":
        initial_workers = rng.randint(4, 15)
        planned_days = rng.randint(3, 12)
        total_work = initial_workers * planned_days
        possible_new_workers = [
            workers
            for workers in range(2, 21)
            if workers != initial_workers and total_work % workers == 0
        ]
        if not possible_new_workers:
            possible_new_workers = [initial_workers + planned_days]
        new_workers = rng.choice(possible_new_workers)
        worker_change = new_workers - initial_workers
        change_text = (
            f"được bổ sung thêm {worker_change} người"
            if worker_change > 0
            else f"rút bớt {abs(worker_change)} người"
        )
        subjects = ["một con đường", "một công việc", "một lô sản phẩm"]
        openings = [
            f"Một tổ gồm {initial_workers} người dự định làm xong {subjects[variant]} trong {planned_days} ngày",
            f"Một đội có {initial_workers} công nhân dự kiến hoàn thành {subjects[variant]} trong {planned_days} ngày",
            f"Một nhóm có {initial_workers} người, theo kế hoạch sẽ hoàn thành {subjects[variant]} trong {planned_days} ngày",
        ]
        stem = (
            f"{openings[variant]}, sau đó tổ {change_text}. "
            "Hỏi công việc hoàn thành trong bao nhiêu ngày, biết sức làm việc của mỗi người như nhau?"
        )
        target = document(
            stem,
            5,
            "ratio",
            family,
            [
                quantity("count_initial", initial_workers, "Số người ban đầu"),
                quantity("duration", planned_days, "Số ngày dự định"),
                quantity("count_change", worker_change, "Mức thay đổi số người"),
            ],
            [unknown("result", "duration", "Số ngày hoàn thành sau khi thay đổi số người")],
            "word_problem",
        )
        return stem, target

    if family == "fraction_power":
        numerator = -rng.randint(2, 8)
        denominator = rng.randint(abs(numerator) + 1, 9)
        exponent = rng.choice([2, 3])
        superscripts = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        exponent_display = str(exponent).translate(superscripts) if index % 2 else f"^{exponent}"
        result_numerator = numerator ** exponent
        result_denominator = denominator ** exponent
        distractors = [
            f"{abs(result_numerator)}/{result_denominator}",
            f"{numerator * exponent}/{denominator * exponent}",
            f"{result_numerator}/{denominator * exponent}",
        ]
        values = list(dict.fromkeys([*distractors, f"{result_numerator}/{result_denominator}"]))
        while len(values) < 4:
            values.append(f"{result_numerator + len(values)}/{result_denominator}")
        rng.shuffle(values)
        choices = [f"{chr(65 + choice_index)}. {value}" for choice_index, value in enumerate(values[:4])]
        lead = ["Kết quả", "Tính", "Quan sát rồi tính"][variant]
        stem = f"{lead} ({numerator}/{denominator}){exponent_display} là"
        displayed = f"{stem}\n" + "\n".join(choices)
        target = document(
            stem,
            7,
            "algebra",
            family,
            [
                quantity("numerator", numerator, "Tử số của cơ số"),
                quantity("denominator", denominator, "Mẫu số của cơ số"),
                quantity("exponent", exponent, "Số mũ"),
            ],
            [unknown("result", "fraction", "Kết quả")],
            "multiple_choice",
            choices=choices,
            extracted_text=displayed,
        )
        return displayed, target

    if family == "fraction_equivalence":
        denominator = rng.randint(2, 9)
        numerator = rng.randint(1, denominator - 1)
        factor = rng.randint(2, 5)
        target_denominator = denominator * factor
        lead = ["Điền tử số thích hợp", "Dùng mô hình phần bằng nhau", "Chia lại thanh phân số rồi hoàn thành"][variant]
        stem = f"{lead}: {numerator}/{denominator} = ?/{target_denominator}."
        data = [
            quantity("numerator", numerator, "Tử số ban đầu"),
            quantity("denominator", denominator, "Mẫu số ban đầu"),
            quantity("target_denominator", target_denominator, "Mẫu số đích"),
        ]
        return stem, document(
            stem,
            4,
            "fraction",
            family,
            data,
            [unknown("result", "number", "Tử số cần điền")],
        )

    if family.startswith("fraction_"):
        left_d = rng.randint(2, 9)
        right_d = rng.randint(2, 9)
        left_n = rng.randint(1, left_d - 1)
        right_n = rng.randint(1, right_d - 1)
        symbol = {
            "fraction_addition": "+",
            "fraction_subtraction": "−",
            "fraction_multiplication": "×",
            "fraction_division": "÷",
        }[family]
        lead = ["Tính", "Hãy biểu diễn rồi tính", "Dùng mô hình phân số để tính"][variant]
        stem = f"{lead} {left_n}/{left_d} {symbol} {right_n}/{right_d} = ?"
        data = [
            quantity("numerator", left_n, "Tử số phân số thứ nhất"),
            quantity("denominator", left_d, "Mẫu số phân số thứ nhất"),
            quantity("addend_numerator", right_n, "Tử số phân số thứ hai"),
            quantity("addend_denominator", right_d, "Mẫu số phân số thứ hai"),
        ]
        return stem, document(stem, 4 if family != "fraction_multiplication" else 5, "fraction", family, data, [unknown("result", "fraction", "Kết quả phép tính")])

    if family in {"place_value_read_write", "decimal_read_write"}:
        if family == "place_value_read_write":
            value = rng.randint(101, 999_999)
            grade = rng.choice([2, 3, 5])
            stems = [
                f"Đặt số {value} vào bảng giá trị hàng rồi đọc số.",
                f"Phân tích số {value} thành tổng các giá trị hàng.",
                f"Dùng khối cơ số 10 để biểu diễn số {value}.",
            ]
        else:
            places = rng.choice([1, 2, 3])
            value = round(rng.randint(10, 9999) / (10 ** places), places)
            grade = 5
            stems = [
                f"Đặt số thập phân {value} vào bảng giá trị hàng.",
                f"Phân tích số {value} thành phần nguyên và các hàng thập phân.",
                f"Biểu diễn số {value} trên bảng giá trị hàng rồi đọc số.",
            ]
        stem = stems[variant]
        return stem, document(
            stem,
            grade,
            "number",
            family,
            [quantity("count", value, "Số đã cho")],
            [unknown("result", "place_value_expansion", "Cách đọc và dạng khai triển")],
        )

    if family == "number_ordering_rounding":
        rounding = index % 2 == 0
        if rounding:
            scale = rng.choice([10, 100, 1000])
            value = rng.randint(11, 9999)
            stem = [f"Làm tròn số {value} đến hàng có giá trị {scale}.", f"Đặt {value} giữa hai mốc bội của {scale} rồi làm tròn.", f"Dùng khoảng cách trên tia số để làm tròn {value} đến {scale}."][variant]
            data = [quantity("count", value, "Số cần làm tròn"), quantity("constant", scale, "Giá trị hàng làm tròn")]
            problem_type = "number_ordering_rounding_rounding"
        else:
            values = rng.sample(range(1, 500), 4)
            stem = [f"Sắp xếp các số {', '.join(map(str, values))} theo thứ tự tăng dần.", f"Đặt các số {', '.join(map(str, values))} lên cùng một tia số.", f"So sánh rồi sắp xếp {', '.join(map(str, values))} từ bé đến lớn."][variant]
            data = [quantity("count", value, f"Số thứ {position + 1}") for position, value in enumerate(values)]
            problem_type = "number_ordering_rounding_ordering"
        return stem, document(stem, rng.choice([1, 3, 6]), "number", problem_type, data, [unknown("result", "ordered_or_rounded_number", "Kết luận")])

    if family == "signed_decimal_fraction_ordering":
        from fractions import Fraction
        fractions = []
        while len(fractions) < 4:
            candidate = Fraction(rng.randint(-12, 12), rng.randint(2, 9))
            if candidate not in fractions:
                fractions.append(candidate)
        labels = [f"{item.numerator}/{item.denominator}" if item.denominator != 1 else str(item.numerator) for item in fractions]
        stem = [f"Sắp xếp các số hữu tỉ {', '.join(labels)} theo thứ tự tăng dần.", f"Đổi và đặt {', '.join(labels)} lên cùng một trục số.", f"So sánh số âm, phân số và thập phân tương ứng của {', '.join(labels)}."][variant]
        data = [quantity("count", float(value), f"Số {label}") for value, label in zip(fractions, labels)]
        return stem, document(stem, 6, "number", family, data, [unknown("result", "ordered_numbers", "Thứ tự các số")])

    if family in {"column_arithmetic_regrouping", "decimal_arithmetic"}:
        # Four operations, not two: a column algorithm that stops at + and −
        # cannot show a partial product or a brought-down digit.
        operation = ("subtraction", "addition", "multiplication", "division")[index % 4]
        subtract = operation == "subtraction"
        if family == "column_arithmetic_regrouping":
            grade = rng.choice([2, 3, 5])
            if operation == "multiplication":
                left = rng.randint(23, 999)
                right = rng.randint(12, 99)
            elif operation == "division":
                right = rng.randint(2, 24)
                left = right * rng.randint(12, 400)
            else:
                left = rng.randint(120, 9999)
                right = rng.randint(11, left - 1)
        else:
            grade = 5
            places = rng.choice([1, 2])
            scale = 10 ** places
            if operation == "multiplication":
                left = round(rng.randint(15, 999) / scale, places)
                right = round(rng.randint(11, 99) / scale, places)
            elif operation == "division":
                right = round(rng.randint(2, 95) / scale, places)
                left = round(right * rng.randint(2, 40), places + 2)
            else:
                left = round(rng.randint(120, 9999) / scale, places)
                right = round(rng.randint(11, max(12, int(left * scale) - 1)) / scale, places)
                if right >= left:
                    left, right = right, left
        symbol = {"subtraction": "−", "addition": "+", "multiplication": "×", "division": ":"}[operation]
        lead = ["Đặt tính rồi tính", "Căn thẳng cột và tính", "Giải thích từng lần nhớ hoặc mượn"][variant]
        stem = f"{lead}: {left} {symbol} {right}."
        return stem, document(
            stem,
            grade,
            "arithmetic",
            f"{family}_{operation}",
            [quantity("count_initial", left, "Số thứ nhất"), quantity("count_change", right, "Số thứ hai")],
            [unknown("result", "number", "Kết quả")],
        )

    if family == "measurement_conversion_comparison":
        pairs = [("km", "m", 1000), ("m", "cm", 100), ("cm", "mm", 10), ("kg", "g", 1000), ("liter", "ml", 1000), ("m2", "cm2", 10_000), ("m3", "cm3", 1_000_000)]
        source_unit, target_unit, _factor = rng.choice(pairs)
        value = rng.randint(1, 25) / rng.choice([1, 1, 2, 4])
        lead = ["Đổi đơn vị", "Dùng thang đơn vị để đổi", "So sánh cùng một đại lượng sau khi đổi"][variant]
        stem = f"{lead}: {value} {source_unit} = ? {target_unit}."
        role = "length" if source_unit in {"km", "m", "cm", "mm"} else ("mass" if source_unit in {"kg", "g"} else ("capacity" if source_unit in {"liter", "ml"} else ("area" if source_unit in {"m2", "cm2"} else "volume")))
        return stem, document(
            stem,
            rng.choice([2, 4, 5]),
            "measurement",
            family,
            [quantity(role, value, "Số đo ban đầu", source_unit)],
            [unknown("result", "measurement", "Số đo sau khi đổi", target_unit)],
        )

    if family in {"picture_bar_chart_reading", "statistics_probability_from_chart"}:
        labels = rng.sample(["Đỏ", "Xanh", "Vàng", "Tím", "Cam", "Hồng"], 4)
        values = [rng.randint(2, 18) for _ in labels]
        rows = ", ".join(f"{label}: {value}" for label, value in zip(labels, values))
        if family == "picture_bar_chart_reading":
            stem = [f"Vẽ biểu đồ cột từ bảng: {rows}. Nhóm nào nhiều nhất?", f"Bảng tần số gồm {rows}. Hãy dựng biểu đồ và đọc cực trị.", f"Biểu diễn dữ liệu {rows} bằng các cột cùng tỉ lệ."][variant]
            grade, domain, kind = rng.choice([2, 3, 5]), "statistics", "chart_reading"
        else:
            stem = [f"Một hộp có các màu {rows}. Dùng biểu đồ để tìm xác suất lấy màu xuất hiện nhiều nhất.", f"Từ bảng tần số {rows}, dựng biểu đồ rồi tính xác suất thực nghiệm.", f"Liên kết biểu đồ với xác suất cho dữ liệu: {rows}."][variant]
            grade, domain, kind = 9, "probability", "probability"
        icon_scale = rng.choice([1, 1, 2])
        data = [quantity("frequency", value, f"Tần số {label}") for label, value in zip(labels, values)]
        data.append(quantity("constant", icon_scale, "Mỗi biểu tượng đại diện"))
        return stem, document(stem, grade, domain, family, data, [unknown("result", kind, "Kết luận từ biểu đồ")], "data_question")

    if family == "experimental_probability":
        total = rng.choice([20, 30, 40, 50, 60])
        success = rng.randint(3, total - 3)
        event = rng.choice(["mặt ngửa", "số chẵn", "màu xanh", "trúng đích"])
        stem = [f"Trong {total} phép thử, biến cố {event} xảy ra {success} lần. Tính xác suất thực nghiệm.", f"Phát lại bảng gồm {total} lần thử với {success} lần {event}, rồi tìm tần số tương đối.", f"Dùng dải phép thử để biểu diễn {success} kết quả thuận lợi trong {total} lần."][variant]
        data = [quantity("frequency", success, f"Số lần {event}"), quantity("count", total, "Tổng số phép thử")]
        return stem, document(stem, 8, "probability", family, data, [unknown("result", "probability", "Xác suất thực nghiệm")], "data_question")

    if family == "percentage_part_whole":
        percent = rng.choice([10, 20, 25, 40, 50, 60, 75, 80])
        whole = rng.choice([20, 40, 50, 80, 100, 200])
        part = whole * percent / 100
        mode = index % 3
        if mode == 0:
            stem = [f"{part} là bao nhiêu phần trăm của {whole}?", f"Tô lưới 100 ô để biểu diễn phần {part} trong toàn bộ {whole}.", f"Đổi tỉ số {part}/{whole} thành phần trăm."][variant]
            data = [quantity("count_change", part, "Phần"), quantity("count_initial", whole, "Toàn bộ")]
            result_kind = "percentage"
        elif mode == 1:
            stem = [f"Tìm {percent}% của {whole}.", f"Toàn bộ là {whole}; dùng lưới 100 ô để tìm phần ứng với {percent}%.", f"Biểu diễn {percent}% của {whole} rồi tìm giá trị phần."][variant]
            data = [quantity("probability", percent, "Tỉ lệ phần trăm"), quantity("count_initial", whole, "Toàn bộ")]
            result_kind = "part"
        else:
            stem = [f"{part} bằng {percent}% của một số. Tìm số đó.", f"Phần {part} chiếm {percent}%; dựng lưới để tìm toàn bộ.", f"Tìm toàn bộ khi biết {part} tương ứng {percent}%."][variant]
            data = [quantity("count_change", part, "Phần"), quantity("probability", percent, "Tỉ lệ phần trăm")]
            result_kind = "whole"
        return stem, document(stem, rng.choice([5, 6]), "ratio", family, data, [unknown("result", result_kind, "Đại lượng cần tìm")], "word_problem")

    if family in {"quadratic_function_graph", "quadratic_equation_vieta"}:
        a = rng.choice([item for item in range(-4, 5) if item])
        vertex_x = rng.randint(-3, 3)
        root_offset = rng.randint(1, 4)
        root_1, root_2 = vertex_x - root_offset, vertex_x + root_offset
        b = -a * (root_1 + root_2)
        c = a * root_1 * root_2
        sign_b, sign_c = ("+" if b >= 0 else "−"), ("+" if c >= 0 else "−")
        if family == "quadratic_function_graph":
            stem = [
                f"Vẽ parabol y = {a}x² {sign_b} {abs(b)}x {sign_c} {abs(c)}.",
                f"Lập bảng giá trị, tìm đỉnh và dựng đồ thị y = {a}x² {sign_b} {abs(b)}x {sign_c} {abs(c)}.",
                f"Biểu diễn hàm bậc hai y = {a}x² {sign_b} {abs(b)}x {sign_c} {abs(c)} trên hệ trục.",
            ][variant]
            result_kind, result_label = "parabola", "Đồ thị hàm số"
        else:
            stem = [
                f"Giải phương trình {a}x² {sign_b} {abs(b)}x {sign_c} {abs(c)} = 0 rồi kiểm tra hệ thức Viète.",
                f"Dùng parabol và Viète để tìm tổng, tích nghiệm của {a}x² {sign_b} {abs(b)}x {sign_c} {abs(c)} = 0.",
                f"Tìm hai nghiệm rồi đối chiếu x₁+x₂=-b/a, x₁x₂=c/a cho {a}x² {sign_b} {abs(b)}x {sign_c} {abs(c)} = 0.",
            ][variant]
            result_kind, result_label = "roots", "Nghiệm và hệ thức Viète"
        data = [quantity("coefficient", a, "Hệ số a"), quantity("coefficient", b, "Hệ số b"), quantity("constant", c, "Hệ số c")]
        return stem, document(stem, 9, "algebra", family, data, [unknown("result", result_kind, result_label)], "construction")

    if family == "triangle_area":
        base, height = rng.randint(3, 18), rng.randint(2, 14)
        stem = [f"Tam giác có đáy {base} cm và chiều cao {height} cm. Tính diện tích.", f"Ghép hai tam giác đáy {base} cm, cao {height} cm thành hình chữ nhật rồi tính diện tích.", f"Dựng tam giác có đáy {base} cm, đường cao {height} cm và tìm diện tích."][variant]
        data = [quantity("length", base, "Đáy", "cm"), quantity("height", height, "Chiều cao", "cm")]
        return stem, document(stem, 5, "geometry_2d", family, data, [unknown("result", "area", "Diện tích", "cm2")], "word_problem")

    if family == "right_triangle_solution":
        # Pythagorean triples keep the third side exact, so a scene never has
        # to present a rounded length as if it were given.
        triple = rng.choice([
            (3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (7, 24, 25),
            (9, 12, 15), (20, 21, 29), (12, 16, 20), (10, 24, 26),
        ])
        scale = rng.choice([1, 1, 1, 2, 3])
        first_leg, second_leg, hypotenuse = (value * scale for value in triple)
        unit = rng.choice(["cm", "dm", "m"])
        first, second, third, right_at = rng.choice([
            ("A", "B", "C", "A"), ("M", "N", "P", "N"), ("D", "E", "F", "E"),
            ("P", "Q", "R", "Q"), ("X", "Y", "Z", "Y"),
        ])
        vertices = f"{first}{second}{third}"
        others = sorted(set(vertices) - {right_at})
        leg_one = "".join(sorted(right_at + others[0]))
        hypotenuse_name = "".join(sorted(others))
        contexts = [
            (f"Hãy giải tam giác {vertices} vuông tại {right_at}. "
             f"Biết {leg_one} = {first_leg} {unit}, {hypotenuse_name} = {hypotenuse} {unit}. "
             "(Góc làm tròn đến phút)."),
            (f"Cho tam giác {vertices} vuông tại {right_at} có {leg_one} = {first_leg} {unit} "
             f"và {hypotenuse_name} = {hypotenuse} {unit}. Giải tam giác {vertices}."),
            (f"Tam giác {vertices} vuông tại {right_at}, cạnh {leg_one} = {first_leg} {unit}, "
             f"cạnh huyền {hypotenuse_name} = {hypotenuse} {unit}. Giải tam giác {vertices}."),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            9,
            "geometry_2d",
            family,
            [
                quantity("length", float(first_leg), f"Cạnh góc vuông {leg_one}", unit),
                quantity("height", float(hypotenuse), f"Cạnh huyền {hypotenuse_name}", unit),
            ],
            [
                unknown("result", "length", "Độ dài cạnh góc vuông còn lại", unit),
                unknown("angle", "angle", f"Số đo góc {others[0]}", "degree"),
                unknown("angle", "angle", f"Số đo góc {others[1]}", "degree"),
            ],
            "word_problem",
        )

    if family == "time_calendar_duration":
        month = rng.choice([1, 3, 4, 5, 6, 9, 10, 11, 12])
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
        start_day = rng.randint(1, days_in_month - 1)
        duration = rng.randint(3, 21)
        weekday = rng.randint(0, 6)
        weekday_names = ["Chủ nhật", "Thứ hai", "Thứ ba", "Thứ tư", "Thứ năm", "Thứ sáu", "Thứ bảy"]
        contexts = [
            (f"Ngày {start_day} tháng {month} là {weekday_names[weekday]}. "
             f"Hỏi sau {duration} ngày nữa là ngày nào?"),
            (f"Một khóa học bắt đầu ngày {start_day}/{month} và kéo dài {duration} ngày. "
             "Hỏi khóa học kết thúc vào ngày nào?"),
            (f"Từ ngày {start_day} tháng {month}, bạn Lan tưới cây liên tục trong {duration} ngày. "
             "Ngày cuối cùng là ngày nào?"),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            rng.choice([3, 5]),
            "time",
            family,
            [
                quantity("count_initial", float(start_day), f"Ngày bắt đầu trong tháng {month}"),
                quantity("duration", float(duration), "Số ngày kéo dài", "day"),
            ],
            [unknown("result", "date", "Ngày kết thúc", None)],
            "word_problem",
            relationships=[{
                "type": "calendar_span",
                "participant_roles": {"start": "count_initial", "duration": "duration"},
                "parameters": {"month": month, "start_weekday": weekday},
                "evidence": EVIDENCE,
            }],
        )

    if family == "algebraic_expression_modeling":
        coefficient = rng.randint(2, 9)
        constant = rng.choice([value for value in range(-12, 13) if value])
        subjects = ["số bút của An", "số tuổi của em", "số quyển vở đã mua"]
        results = ["số bút của Bình", "số tuổi của anh", "số quyển vở của lớp"]
        subject = subjects[variant]
        result_label = results[variant]
        comparison = (
            f"hơn {constant} đơn vị" if constant > 0 else f"kém {abs(constant)} đơn vị"
        )
        stem = (
            f"Gọi x là {subject}. Biết {result_label} gấp {coefficient} lần {subject} và {comparison}. "
            f"Hãy viết biểu thức biểu thị {result_label} theo x."
        )
        return stem, document(
            stem,
            7,
            "algebra",
            family,
            [
                quantity("coefficient", float(coefficient), f"Hệ số của {subject}"),
                quantity("constant", float(constant), "Hằng số so sánh"),
            ],
            [unknown("result", "expression", f"Biểu thức biểu thị {result_label}")],
            "word_problem",
            relationships=[{
                "type": "expression_model",
                "participant_roles": {"coefficient": "coefficient", "constant": "constant"},
                "parameters": {"symbol": "x", "subject": subject, "result": result_label},
                "evidence": EVIDENCE,
            }],
        )

    if family == "triangle_congruence_centroid_proof":
        # Keep the median a multiple of 3 so both parts stay exact, and vary the
        # vertex names: one split alone needs eighty distinct stems.
        median = rng.choice([value for value in range(6, 121) if value % 3 == 0])
        unit = rng.choice(["cm", "dm", "m"])
        first, second, third, midpoint = rng.choice([
            ("A", "B", "C", "M"), ("M", "N", "P", "I"), ("D", "E", "F", "K"),
            ("P", "Q", "R", "H"), ("X", "Y", "Z", "T"),
        ])
        triangle = f"{first}{second}{third}"
        median_name = f"{first}{midpoint}"
        contexts = [
            (f"Tam giác {triangle} có trung tuyến {median_name} dài {median} {unit}, "
             "G là trọng tâm. Tính độ dài "
             f"{first}G và G{midpoint}."),
            (f"Cho tam giác {triangle}, {midpoint} là trung điểm {second}{third} và "
             f"{median_name} = {median} {unit}. Trọng tâm G chia {median_name} theo tỉ số nào "
             "và mỗi phần dài bao nhiêu?"),
            (f"Trung tuyến {median_name} của tam giác {triangle} dài {median} {unit}. "
             f"Hỏi khoảng cách từ đỉnh {first} đến trọng tâm G bằng bao nhiêu?"),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            7,
            "geometry_2d",
            "triangle_centroid_median_proof",
            [quantity("length", float(median), f"Độ dài trung tuyến {median_name}", unit)],
            [unknown("result", "length", f"Độ dài {first}G và G{midpoint}", unit)],
            "word_problem",
        )

    if family == "triangle_similarity_metric_relation":
        small_a = rng.randint(2, 9)
        small_b = rng.randint(2, 9)
        factor = rng.randint(2, 5)
        large_a = small_a * factor
        unit = rng.choice(["cm", "dm"])
        contexts = [
            (f"Tam giác ABC và tam giác A'B'C' đồng dạng. Biết AB = {small_a} {unit}, "
             f"AC = {small_b} {unit} và A'B' = {large_a} {unit}. Tính A'C'."),
            (f"Hai tam giác đồng dạng có cặp cạnh tương ứng AB = {small_a} {unit} và "
             f"A'B' = {large_a} {unit}. Nếu AC = {small_b} {unit} thì A'C' bằng bao nhiêu?"),
            (f"Cho tam giác ABC đồng dạng với tam giác A'B'C', AB = {small_a} {unit}, "
             f"AC = {small_b} {unit}, A'B' = {large_a} {unit}. Tìm độ dài cạnh A'C'."),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            8,
            "geometry_2d",
            family,
            [
                quantity("length", float(small_a), "Cạnh AB của tam giác nhỏ", unit),
                quantity("length", float(small_b), "Cạnh AC của tam giác nhỏ", unit),
                quantity("height", float(large_a), "Cạnh A'B' tương ứng của tam giác lớn", unit),
            ],
            [unknown("result", "length", "Độ dài cạnh A'C'", unit)],
            "word_problem",
        )

    if family == "word_equation_rectangle":
        difference = rng.randint(2, 15)
        width = rng.randint(3, 30)
        length = width + difference
        perimeter = 2 * (length + width)
        unit = rng.choice(["m", "cm"])
        contexts = [
            (f"Một hình chữ nhật có chu vi {perimeter} {unit} và chiều dài hơn chiều rộng "
             f"{difference} {unit}. Tính chiều dài và chiều rộng của hình chữ nhật."),
            (f"Mảnh vườn hình chữ nhật có chu vi {perimeter} {unit}, chiều dài hơn chiều rộng "
             f"{difference} {unit}. Hỏi mỗi kích thước bằng bao nhiêu?"),
            (f"Chu vi một hình chữ nhật là {perimeter} {unit}. Chiều dài lớn hơn chiều rộng "
             f"{difference} {unit}. Tìm hai kích thước đó."),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            8,
            "algebra",
            family,
            [
                quantity("total", float(perimeter), f"Chu vi hình chữ nhật ({unit})"),
                quantity("count_change", float(difference), f"Chiều dài hơn chiều rộng ({unit})"),
            ],
            [unknown("result", "length", "Chiều dài và chiều rộng", unit)],
            "word_problem",
        )

    if family == "mixed_rational_arithmetic_percent":
        from fractions import Fraction as _Fraction

        first = _Fraction(rng.randint(1, 7), rng.randint(2, 9))
        second = _Fraction(rng.randint(1, 7), rng.randint(2, 9))
        third_percent = rng.choice([10, 20, 25, 40, 50, 60, 75])
        third = _Fraction(third_percent, 100)
        operators = rng.choice([["+", "×"], ["−", "×"], ["+", "÷"], ["×", "+"]])
        labels = [
            f"{first.numerator}/{first.denominator}",
            f"{second.numerator}/{second.denominator}",
            f"{third_percent}%",
        ]
        expression = f"{labels[0]} {operators[0]} {labels[1]} {operators[1]} {labels[2]}"
        lead = ["Tính giá trị biểu thức", "Thực hiện phép tính", "Tính rồi rút gọn"][variant]
        stem = f"{lead}: {expression}."
        return stem, document(
            stem,
            6,
            "fraction",
            "mixed_rational_expression",
            [
                quantity("count", float(first), f"Số hạng {labels[0]}"),
                quantity("count", float(second), f"Số hạng {labels[1]}"),
                quantity("count", float(third), f"Số hạng {labels[2]}"),
            ],
            [unknown("result", "number", "Giá trị biểu thức")],
            "short_answer",
            relationships=[{
                "type": "expression_tree",
                "participant_roles": {
                    "first": "count[1]",
                    "second": "count[2]",
                    "third": "count[3]",
                },
                "parameters": {"operators": operators, "operand_labels": labels},
                "evidence": EVIDENCE,
            }],
        )

    if family == "discount_tax_percentage":
        original = rng.randint(2, 60) * 10_000
        discount = rng.choice([5, 10, 15, 20, 25, 30, 40, 50])
        tax = rng.choice([0, 5, 8, 10])
        tax_clause = f" rồi chịu thêm thuế {tax}%" if tax else ""
        contexts = [
            (f"Một chiếc áo có giá niêm yết {original} đồng, được giảm giá {discount}%{tax_clause}. "
             "Hỏi khách phải trả bao nhiêu tiền?"),
            (f"Cửa hàng giảm {discount}% cho món hàng giá {original} đồng{tax_clause}. "
             "Tính số tiền phải thanh toán."),
            (f"Giá gốc của một quyển sách là {original} đồng. Sau khi giảm {discount}%{tax_clause}, "
             "khách trả bao nhiêu đồng?"),
        ]
        stem = contexts[variant]
        quantities = [
            quantity("count_initial", float(original), "Giá niêm yết (đồng)"),
            quantity("probability", float(discount), "Mức giảm giá (%)"),
        ]
        if tax:
            quantities.append(quantity("probability", float(tax), "Mức thuế (%)"))
        return stem, document(
            stem,
            6,
            "ratio",
            family,
            quantities,
            [unknown("result", "money", "Số tiền phải trả")],
            "word_problem",
        )

    if family == "two_item_discount_system":
        # Keep the prices as unknowns.  The last statement is deliberately a
        # claim to verify, not a pair of known quantities copied into the SFT
        # target.  Prices are multiples of 20,000 so every 5% discount remains
        # an exact number of dong and the semantic oracle has no rounding noise.
        first_price = rng.randint(4, 12) * 20_000
        second_price = rng.randint(4, 12) * 20_000
        first_discount = rng.choice([5, 10, 15, 20, 25])
        second_discount = rng.choice([
            rate for rate in [5, 10, 15, 20, 25, 30] if rate != first_discount
        ])
        list_total = first_price + second_price
        paid_total = (
            first_price * (100 - first_discount)
            + second_price * (100 - second_discount)
        ) // 100
        claimed_first, claimed_second = (
            (second_price, first_price) if variant != 1 else (first_price, second_price)
        )
        leads = [
            "Bạn An mua một quyển sách bồi dưỡng Toán và một quyển sách bồi dưỡng Ngữ Văn",
            "Minh chọn một sách tham khảo Toán và một sách tham khảo Ngữ Văn",
            "Một học sinh mua một quyển sách Toán và một quyển sách Ngữ Văn",
        ]
        stem = (
            f"{leads[variant]} với tổng số tiền theo giá niêm yết là {list_total} đồng. "
            f"Sách Toán được giảm giá {first_discount}%; sách Ngữ Văn được giảm giá "
            f"{second_discount}%. Do đó người mua chỉ phải trả {paid_total} đồng. "
            "Gọi giá niêm yết của sách Toán và sách Ngữ Văn lần lượt là x, y (đồng). "
            f"Khẳng định: giá niêm yết của sách Toán là {claimed_first} đồng và sách "
            f"Ngữ Văn là {claimed_second} đồng. Hãy kiểm tra khẳng định."
        )
        return stem, document(
            stem,
            9,
            "algebra",
            family,
            [
                quantity("total", float(list_total), "Tổng giá niêm yết của hai quyển sách (đồng)"),
                quantity("total", float(paid_total), "Tổng số tiền thực trả (đồng)"),
                quantity("probability", float(first_discount), "Mức giảm của Sách Toán (%)"),
                quantity("probability", float(second_discount), "Mức giảm của Sách Ngữ Văn (%)"),
            ],
            [
                unknown("variable", "money", "Giá niêm yết Sách Toán (x, đồng)"),
                unknown("variable", "money", "Giá niêm yết Sách Ngữ Văn (y, đồng)"),
            ],
            "word_problem",
            relationships=[{
                "type": family,
                "participant_roles": {
                    "list_total": "total[1]",
                    "paid_total": "total[2]",
                    "first_discount": "probability[1]",
                    "second_discount": "probability[2]",
                    "first_price": "variable[1]",
                    "second_price": "variable[2]",
                },
                "parameters": {
                    "first_label": "Sách Toán",
                    "second_label": "Sách Ngữ Văn",
                    "first_symbol": "x",
                    "second_symbol": "y",
                    "claimed_first": claimed_first,
                    "claimed_second": claimed_second,
                },
                "evidence": EVIDENCE,
            }],
        )

    if family == "multi_segment_equal_distance_motion":
        distance = rng.choice([12, 18, 24, 30, 36, 45, 60])
        first_speed = rng.choice([6, 9, 12, 15, 18])
        second_speed = rng.choice([speed for speed in (10, 20, 24, 30, 36, 40) if speed != first_speed])
        contexts = [
            (f"Một người đi từ A đến B dài {distance} km với vận tốc {first_speed} km/giờ, "
             f"rồi đi tiếp {distance} km nữa với vận tốc {second_speed} km/giờ. "
             "Hỏi tổng thời gian và vận tốc trung bình của cả hành trình?"),
            (f"Xe đạp đi chặng đầu {distance} km hết với vận tốc {first_speed} km/giờ và chặng sau "
             f"{distance} km với vận tốc {second_speed} km/giờ. Tính vận tốc trung bình cả quãng đường."),
            (f"Một ô tô chạy {distance} km đầu với vận tốc {first_speed} km/giờ, "
             f"{distance} km sau với vận tốc {second_speed} km/giờ. "
             "Hỏi thời gian cả hành trình là bao lâu?"),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            7,
            "motion",
            "multi_segment_equal_distance_motion",
            [
                quantity("distance", float(distance), "Quãng đường chặng một", "km"),
                quantity("distance", float(distance), "Quãng đường chặng hai", "km"),
                quantity("speed", float(first_speed), "Vận tốc chặng một", "km/h"),
                quantity("speed", float(second_speed), "Vận tốc chặng hai", "km/h"),
            ],
            [unknown("result", "duration", "Tổng thời gian của hành trình", "hour")],
            "word_problem",
            entities=[{
                "role": "moving_entity",
                "type": "vehicle",
                "label": "Phương tiện",
                "evidence": EVIDENCE,
            }],
        )

    if family == "compound_linear_equation":
        multiplier = rng.randint(2, 6)
        inner_constant = rng.randint(1, 9)
        outer_constant = rng.randint(1, 12)
        right_coefficient = rng.randint(1, multiplier - 1)
        solution = rng.randint(1, 12)
        left_value = multiplier * (solution + inner_constant) - outer_constant
        right_constant = left_value - right_coefficient * solution
        # A coefficient of 1 is not written on a blackboard.
        right_term = "x" if right_coefficient == 1 else f"{right_coefficient}x"
        tail = (
            f"+ {right_constant}" if right_constant >= 0 else f"- {abs(right_constant)}"
        )
        equation = (
            f"{multiplier}(x + {inner_constant}) - {outer_constant} = {right_term} {tail}"
        )
        lead = ["Giải phương trình", "Tìm x biết", "Phá ngoặc rồi giải phương trình"][variant]
        stem = f"{lead} {equation}."
        return stem, document(
            stem,
            8,
            "algebra",
            family,
            [
                quantity("coefficient", float(multiplier - right_coefficient), "Hệ số của x sau khi thu gọn"),
                quantity("constant", 0.0, "Hằng số ở vế trái sau khi chuyển vế"),
                quantity("result", float(right_constant + outer_constant - multiplier * inner_constant), "Vế phải sau khi chuyển vế"),
            ],
            [unknown("variable", "variable", "Giá trị của x")],
            "short_answer",
        )

    if family == "arithmetic_mean":
        count = rng.choice([3, 4, 5])
        base = rng.randint(10, 90)
        values = [base + rng.randint(-8, 8) * 1 for _ in range(count)]
        total = sum(values)
        # Keep the mean a whole number so the level line lands on a tick.
        values[-1] += (count - total % count) % count
        contexts = [
            ("Một tổ trồng cây trong {count} ngày, số cây trồng được lần lượt là {listed}. "
             "Hỏi trung bình mỗi ngày tổ đó trồng được bao nhiêu cây?"),
            ("Trung bình cộng của {count} số {listed} bằng bao nhiêu?"),
            ("Một cửa hàng bán hàng trong {count} buổi được lần lượt {listed} sản phẩm. "
             "Trung bình mỗi buổi bán được bao nhiêu sản phẩm?"),
        ]
        listed = ", ".join(str(value) for value in values)
        stem = contexts[variant].format(count=count, listed=listed)
        return stem, document(
            stem,
            4,
            "arithmetic",
            family,
            [
                quantity("count_change", value, f"Số liệu thứ {position}")
                for position, value in enumerate(values, start=1)
            ],
            [unknown("result", "number", "Trung bình cộng")],
            "word_problem" if variant != 1 else "short_answer",
        )

    if family == "ratio_total_parts":
        first_parts = rng.randint(1, 7)
        second_parts = rng.choice([value for value in range(1, 8) if value != first_parts])
        one_part = rng.randint(3, 30)
        total = (first_parts + second_parts) * one_part
        contexts = [
            (f"Hai lớp trồng được tất cả {total} cây. Số cây lớp 4A và lớp 4B tỉ lệ với "
             f"{first_parts} và {second_parts}. Hỏi mỗi lớp trồng được bao nhiêu cây?"),
            (f"Tổng của hai số là {total} và tỉ số của chúng là {first_parts}/{second_parts}. Tìm hai số đó."),
            (f"Một kho có {total} kg gạo chia thành hai phần theo tỉ số {first_parts} : {second_parts}. "
             "Tính khối lượng mỗi phần."),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            4,
            "ratio",
            family,
            [
                quantity("total", total, "Tổng hai đại lượng"),
                quantity("numerator", first_parts, "Số phần của đại lượng thứ nhất"),
                quantity("denominator", second_parts, "Số phần của đại lượng thứ hai"),
            ],
            [unknown("result", "number", "Giá trị hai đại lượng")],
            "word_problem",
        )

    if family == "proportional_system_two_variables":
        first_parts = rng.randint(2, 9)
        second_parts = rng.choice([value for value in range(1, 9) if value != first_parts])
        one_part = rng.randint(3, 25)
        difference = abs(first_parts - second_parts) * one_part
        larger, smaller = max(first_parts, second_parts), min(first_parts, second_parts)
        contexts = [
            (f"Hai kho hàng có số hàng tỉ lệ với {larger} và {smaller}. Kho thứ nhất nhiều hơn "
             f"kho thứ hai {difference} tấn. Hỏi mỗi kho có bao nhiêu tấn hàng?"),
            (f"Hiệu của hai số là {difference} và tỉ số của chúng là {larger}/{smaller}. Tìm hai số đó."),
            (f"Số học sinh nam và nữ của một trường tỉ lệ với {larger} và {smaller}, "
             f"số nam nhiều hơn số nữ {difference} bạn. Tính số học sinh mỗi loại."),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            7,
            "ratio",
            family,
            [
                quantity("count_change", difference, "Hiệu hai đại lượng"),
                quantity("numerator", larger, "Số phần của đại lượng lớn"),
                quantity("denominator", smaller, "Số phần của đại lượng nhỏ"),
            ],
            [unknown("result", "number", "Giá trị hai đại lượng")],
            "word_problem",
        )

    if family == "multi_step_arithmetic_word":
        start = rng.randint(40, 400)
        removed = rng.randint(5, min(60, start - 10))
        added = rng.randint(5, 60)
        contexts = [
            (f"Một cửa hàng có {start} quyển vở. Buổi sáng bán {removed} quyển, buổi chiều nhập thêm "
             f"{added} quyển. Hỏi cửa hàng còn bao nhiêu quyển vở?"),
            (f"Trên xe có {start} hành khách. Đến bến thứ nhất có {removed} người xuống, "
             f"đến bến thứ hai có {added} người lên. Hỏi trên xe còn bao nhiêu hành khách?"),
            (f"Một bể chứa {start} lít nước. Người ta lấy ra {removed} lít rồi bơm thêm {added} lít. "
             "Hỏi trong bể có bao nhiêu lít nước?"),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            3,
            "arithmetic",
            "multi_step_arithmetic_subtract_then_add",
            [
                quantity("count_initial", start, "Số lượng ban đầu"),
                quantity("count_change", removed, "Số lượng giảm ở bước một"),
                quantity("count_change", added, "Số lượng tăng ở bước hai"),
            ],
            [unknown("result", "number", "Số lượng còn lại sau hai bước")],
            "word_problem",
        )

    if family == "map_scale":
        denominator = rng.choice([100, 200, 500, 1000, 2000, 5000, 10000, 100000])
        map_length = rng.randint(2, 25)
        contexts = [
            (f"Trên bản đồ tỉ lệ 1 : {denominator}, quãng đường từ A đến B đo được {map_length} cm. "
             "Hỏi quãng đường thật dài bao nhiêu?"),
            (f"Một mảnh đất vẽ trên bản đồ tỉ lệ 1 : {denominator} có chiều dài {map_length} cm. "
             "Tính chiều dài thật của mảnh đất."),
            (f"Bản đồ tỉ lệ 1 : {denominator}. Đoạn thẳng biểu diễn con đường dài {map_length} cm. "
             "Con đường đó dài bao nhiêu trên thực tế?"),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            4,
            "measurement",
            family,
            [
                quantity("length", map_length, "Độ dài đo trên bản đồ", "cm"),
                quantity("coefficient", denominator, "Mẫu số của tỉ lệ bản đồ"),
            ],
            [unknown("result", "length", "Độ dài thật", "m")],
            "word_problem",
        )

    if family == "circle_area":
        radius = rng.randint(2, 25)
        center = rng.choice(["O", "I", "S"])
        # Only units with a registered squared form, so the unknown area unit
        # stays inside the schema instead of inventing "dm2".
        unit = rng.choice(["cm", "m"])
        if index % 3 == 2:
            diameter = radius * 2
            stem = [
                f"Hình tròn tâm {center} có đường kính {diameter} {unit}. Tính diện tích hình tròn.",
                f"Cho hình tròn tâm {center}, đường kính {diameter} {unit}. Diện tích hình tròn đó là bao nhiêu?",
                f"Một mặt bàn hình tròn tâm {center} có đường kính {diameter} {unit}. Tính diện tích mặt bàn.",
            ][variant]
            data = [quantity("diameter", diameter, "Đường kính hình tròn", unit)]
        else:
            stem = [
                f"Hình tròn tâm {center} có bán kính {radius} {unit}. Tính diện tích hình tròn.",
                f"Cho hình tròn tâm {center}, bán kính {radius} {unit}. Diện tích hình tròn đó là bao nhiêu?",
                f"Một tấm bìa hình tròn tâm {center} có bán kính {radius} {unit}. Tính diện tích tấm bìa.",
            ][variant]
            data = [quantity("radius", radius, "Bán kính hình tròn", unit)]
        return stem, document(
            stem,
            5,
            "geometry_2d",
            family,
            data,
            [unknown("result", "area", "Diện tích hình tròn", f"{unit}2")],
            "word_problem",
        )

    if family == "circle_tangent_cyclic_proof":
        radius = rng.randint(3, 12)
        central_angle = rng.choice([40, 50, 60, 70, 80, 90, 100, 110, 120, 140])
        unit = rng.choice(["cm", "dm"])
        stem = [
            f"Cho đường tròn tâm O bán kính {radius} {unit}, tiếp tuyến tại A và hai điểm A, B trên đường tròn "
            f"sao cho góc ở tâm ∠AOB = {central_angle}°. Tính góc nội tiếp ∠AMB cùng chắn cung AB.",
            f"Đường tròn (O; {radius} {unit}) có tiếp tuyến tại A. Biết ∠AOB = {central_angle}°, "
            "hãy tìm số đo góc nội tiếp ∠AMB chắn cung AB.",
            f"Cho (O; {radius} {unit}) với tiếp tuyến tại A vuông góc OA. Góc ở tâm ∠AOB bằng {central_angle}°. "
            "Số đo góc nội tiếp ∠AMB chắn cùng cung AB là bao nhiêu?",
        ][variant]
        return stem, document(
            stem,
            9,
            "geometry_2d",
            family,
            [
                quantity("radius", radius, "Bán kính đường tròn", unit),
                quantity("angle", central_angle, "Góc ở tâm chắn cung AB", "degree"),
            ],
            [unknown("result", "angle", "Số đo góc nội tiếp cùng chắn cung AB", "degree")],
            "word_problem",
        )

    if family == "divisibility_common_multiple":
        first = rng.randint(2, 12)
        second = rng.choice([value for value in range(2, 13) if value != first])
        contexts = [
            (f"Hai xe buýt cùng rời bến. Xe thứ nhất cứ {first} phút chạy một chuyến, "
             f"xe thứ hai cứ {second} phút chạy một chuyến. Hỏi sau ít nhất bao nhiêu phút hai xe lại cùng rời bến?"),
            (f"Tìm bội chung nhỏ nhất của {first} và {second}."),
            (f"Hai đèn nhấp nháy cùng lúc. Đèn thứ nhất nhấp nháy sau mỗi {first} giây, "
             f"đèn thứ hai sau mỗi {second} giây. Sau ít nhất bao nhiêu giây hai đèn lại cùng nhấp nháy?"),
        ]
        stem = contexts[variant]
        return stem, document(
            stem,
            4,
            "number",
            family,
            [
                quantity("count_initial", first, "Số thứ nhất"),
                quantity("count_change", second, "Số thứ hai"),
            ],
            [unknown("result", "number", "Bội chung nhỏ nhất")],
            "word_problem" if variant != 1 else "short_answer",
        )

    if family == "circle_radius_diameter":
        radius = rng.randint(2, 30)
        center = rng.choice(["O", "I", "S"])
        unit = rng.choice(["cm", "dm", "m"])
        given_radius = index % 2 == 0
        if given_radius:
            stem = [f"Đường tròn tâm {center} có bán kính {radius} {unit}. Tìm đường kính.", f"Dựng hai bán kính thẳng hàng của đường tròn tâm {center}, bán kính {radius} {unit}.", f"Biểu diễn quan hệ giữa bán kính {radius} {unit} và đường kính của đường tròn tâm {center}."][variant]
            data = [quantity("radius", radius, "Bán kính", unit)]
        else:
            diameter = radius * 2
            stem = [f"Đường tròn tâm {center} có đường kính {diameter} {unit}. Tìm bán kính.", f"Chia đường kính {diameter} {unit} tại tâm {center} để tìm bán kính.", f"Biểu diễn đường kính {diameter} {unit} bằng hai bán kính của đường tròn tâm {center}."][variant]
            data = [quantity("diameter", diameter, "Đường kính", unit)]
        return stem, document(stem, rng.choice([3, 5]), "geometry_2d", family, data, [unknown("result", "length", "Độ dài cần tìm", unit)])

    if family == "rhombus_parallelogram_area_properties":
        rhombus = index % 2 == 0
        base, height = rng.randint(4, 16), rng.randint(2, 12)
        side = base if rhombus else rng.randint(3, 14)
        shape = "hình thoi" if rhombus else "hình bình hành"
        problem_type = "rhombus_area_properties" if rhombus else "parallelogram_area_properties"
        stem = [f"{shape.title()} có đáy {base} cm, chiều cao {height} cm. Tính diện tích.", f"Cắt và ghép {shape} đáy {base} cm, cao {height} cm thành hình chữ nhật.", f"Dựng {shape} có đáy {base} cm và đường cao {height} cm rồi tìm diện tích."][variant]
        data = [quantity("length", base, "Đáy", "cm"), quantity("height", height, "Chiều cao", "cm"), quantity("width", side, "Cạnh bên", "cm")]
        return stem, document(stem, 4, "geometry_2d", problem_type, data, [unknown("result", "area", "Diện tích", "cm2")], "word_problem")

    if family == "ray_segment_midpoint":
        length = rng.choice([item for item in range(4, 41) if item % 2 == 0])
        point_a, point_b, midpoint = rng.choice([
            ("A", "B", "M"), ("C", "D", "I"), ("P", "Q", "N"),
        ])
        unit = rng.choice(["cm", "dm", "m"])
        segment = f"{point_a}{point_b}"
        first_half = f"{point_a}{midpoint}"
        second_half = f"{midpoint}{point_b}"
        stem = [f"Vẽ đoạn thẳng {segment} dài {length} {unit}, tia {segment} và đánh dấu trung điểm {midpoint}.", f"Phân biệt đoạn {segment} với tia {segment}; biết {segment} = {length} {unit}, tìm {first_half} khi {midpoint} là trung điểm.", f"Dựng {point_a}, {point_b}, trung điểm {midpoint} trên đoạn dài {length} {unit} và kiểm tra {first_half} = {second_half}."][variant]
        return stem, document(stem, 6, "geometry_2d", family, [quantity("length", length, f"Độ dài {segment}", unit)], [unknown("result", "length", "Độ dài một nửa", unit)], "construction")

    if family == "angle_bisector":
        whole_angle = rng.choice([value for value in range(20, 171, 10) if value % 2 == 0])
        first_ray, second_ray, bisector_ray = rng.choice([
            ("x", "y", "t"), ("a", "b", "c"), ("m", "n", "u"),
            ("p", "q", "v"), ("A", "B", "C"), ("M", "N", "P"),
        ])
        whole_name = f"{first_ray}O{second_ray}"
        first_half = f"{first_ray}O{bisector_ray}"
        second_half = f"{bisector_ray}O{second_ray}"
        stems = [
            f"Cho ∠{whole_name} = {whole_angle}°, O{bisector_ray} là tia phân giác của ∠{whole_name}. Số đo ∠{first_half} bằng bao nhiêu?",
            f"Vẽ góc {whole_name} bằng {whole_angle}° rồi dựng tia phân giác O{bisector_ray}. Tìm số đo hai góc bằng nhau.",
            f"Tia O{bisector_ray} chia góc {whole_name} = {whole_angle}° thành hai góc bằng nhau. Hãy xác định ∠{second_half}.",
        ]
        stem = stems[variant]
        return stem, document(
            stem,
            7,
            "geometry_2d",
            family,
            [quantity("angle", whole_angle, "Số đo góc xOy", "degree")],
            [unknown("result", "angle", "Số đo góc do tia phân giác tạo ra", "degree")],
            "construction",
        )

    if family in {"addition", "subtraction"}:
        if family == "addition":
            left, change = rng.randint(2, 40), rng.randint(1, 20)
            stem = [f"Có {left} quả táo, thêm {change} quả. Hỏi có tất cả bao nhiêu quả?", f"Trên bàn có {left} viên bi rồi đặt thêm {change} viên. Có tất cả bao nhiêu viên?", f"Minh có {left} nhãn vở và được cho thêm {change} nhãn. Minh có bao nhiêu nhãn?"][variant]
            change_label = "Số lượng thêm"
            unknown_label = "Tổng số lượng"
        else:
            left = rng.randint(8, 40)
            change = rng.randint(1, left - 1)
            stem = [f"Có {left} quả cam, lấy đi {change} quả. Hỏi còn lại bao nhiêu quả?", f"Hộp có {left} viên bi, bạn An cho đi {change} viên. Hộp còn bao nhiêu viên?", f"Trên cành có {left} con chim, {change} con bay đi. Còn lại bao nhiêu con?"][variant]
            change_label = "Số lượng bớt đi"
            unknown_label = "Số lượng còn lại"
        return stem, document(
            stem,
            2,
            "arithmetic",
            family,
            [
                quantity("count_initial", left, "Số lượng ban đầu"),
                quantity("count_change", change, change_label),
            ],
            [unknown("result", "count", unknown_label)],
            "word_problem",
        )

    if family == "missing_number_equation":
        first, second = rng.randint(2, 30), rng.randint(1, 20)
        total = first + second
        mode = index % 3
        if mode == 0:
            stem = [f"Điền số thích hợp: {first} + {second} = ?.", f"Dùng sơ đồ phần–toàn bộ để tìm ô trống trong {first} + {second} = □.", f"Ghép hai phần {first} và {second}, tìm toàn bộ."][variant]
            data = [quantity("count_initial", first, "Phần thứ nhất"), quantity("count_change", second, "Phần thứ hai")]
            missing = unknown("total", "count", "Toàn bộ")
        elif mode == 1:
            stem = [f"Điền số thích hợp: ? + {second} = {total}.", f"Toàn bộ {total} gồm một phần {second} và một phần chưa biết.", f"Dùng phép tính ngược để điền □ + {second} = {total}."][variant]
            data = [quantity("count_change", second, "Phần đã biết"), quantity("total", total, "Toàn bộ")]
            missing = unknown("count_initial", "count", "Phần còn thiếu")
        else:
            stem = [f"Điền số thích hợp: {first} + ? = {total}.", f"Tìm phần còn thiếu khi toàn bộ là {total} và một phần là {first}.", f"Dùng sơ đồ để điền {first} + □ = {total}."][variant]
            data = [quantity("count_initial", first, "Phần đã biết"), quantity("total", total, "Toàn bộ")]
            missing = unknown("count_change", "count", "Phần còn thiếu")
        return stem, document(stem, rng.choice([1, 2]), "arithmetic", family, data, [missing])

    if family == "shape_recognition_counting_pattern":
        shape_names = {"circle": "hình tròn", "square": "hình vuông", "triangle": "hình tam giác", "rectangle": "hình chữ nhật"}
        pattern_mode = index % 2 == 0
        if pattern_mode:
            cycle = rng.sample(list(shape_names), rng.choice([2, 3]))
            types = (cycle * 3)[: rng.choice([5, 6, 7])]
            stem = [f"Quan sát dãy {', '.join(shape_names[item] for item in types)}. Hình nào tiếp theo?", f"Đánh dấu chu kỳ lặp trong dãy {', '.join(shape_names[item] for item in types)}.", f"Khoanh từng hình rồi tiếp diễn quy luật: {', '.join(shape_names[item] for item in types)}."][variant]
            result_kind = "next_shape"
        else:
            types = [rng.choice(list(shape_names)) for _ in range(rng.randint(6, 10))]
            target = rng.choice(list(shape_names))
            stem = [f"Đếm {shape_names[target]} trong nhóm: {', '.join(shape_names[item] for item in types)}.", f"Khoanh và đánh số từng hình rồi cho biết có bao nhiêu {shape_names[target]}.", f"Phân loại dãy {', '.join(shape_names[item] for item in types)} và đếm {shape_names[target]}."][variant]
            result_kind = "shape_count"
        entities = [{"role": f"shape_{position + 1}", "type": shape_type, "label": shape_names[shape_type], "evidence": EVIDENCE} for position, shape_type in enumerate(types)]
        return stem, document(stem, rng.choice([1, 2]), "geometry_2d", family, [], [unknown("result", result_kind, "Kết quả hình học")], entities=entities)

    if family in {"multiplication_grouping", "division_grouping"}:
        groups, per_group = rng.randint(2, 10), rng.randint(2, 10)
        if family == "multiplication_grouping":
            stem = [f"Có {groups} nhóm, mỗi nhóm {per_group} chấm tròn. Có tất cả bao nhiêu chấm?", f"Xếp {groups} hàng, mỗi hàng {per_group} khối. Hỏi có bao nhiêu khối?", f"Vẽ mảng {groups} × {per_group} rồi tìm tổng số ô."][variant]
            data = [quantity("count_initial", groups, "Số nhóm"), quantity("count_change", per_group, "Số phần tử mỗi nhóm")]
        else:
            total = groups * per_group
            stem = [f"Chia đều {total} chấm tròn, mỗi nhóm {per_group} chấm. Có bao nhiêu nhóm?", f"Xếp {total} khối thành các hàng, mỗi hàng {per_group} khối. Có bao nhiêu hàng?", f"Tách {total} vật thành các nhóm {per_group} vật. Tìm số nhóm."][variant]
            data = [quantity("count_initial", total, "Tổng số phần tử"), quantity("count_change", per_group, "Số phần tử mỗi nhóm")]
        return stem, document(stem, 3, "arithmetic", family, data, [unknown("result", "count", "Số lượng cần tìm")], "word_problem")

    if family == "ratio_from_known_value":
        denominator = rng.randint(2, 6)
        numerator = rng.randint(1, denominator)
        one_part = rng.randint(2, 8)
        known = denominator * one_part
        stem = [f"Số học sinh nữ bằng {numerator}/{denominator} số học sinh nam. Có {known} học sinh nam. Hỏi có bao nhiêu học sinh nữ?", f"Tổ A bằng {numerator}/{denominator} tổ B. Tổ B có {known} bạn. Tìm số bạn tổ A.", f"Một đoạn đỏ dài bằng {numerator}/{denominator} đoạn xanh. Đoạn xanh dài {known} cm. Tìm độ dài đoạn đỏ."][variant]
        data = [quantity("numerator", numerator, "Số phần cần tìm"), quantity("denominator", denominator, "Số phần đã biết"), quantity("count_initial", known, "Đại lượng đã biết")]
        return stem, document(stem, 4, "ratio", family, data, [unknown("result", "count", "Đại lượng theo tỉ số")], "word_problem")

    if family == "sequential_fraction_remainder_ratio":
        first_denominator = 8
        first_numerator = rng.randint(1, 6)
        second_denominator = 4
        second_numerator = rng.randint(1, 3)
        total = 32 * rng.randint(3, 12)
        stem = [
            f"Một cửa hàng có {total}kg gạo và bán hết trong 3 ngày. Ngày thứ nhất bán {first_numerator}/{first_denominator} số gạo. Ngày thứ hai bán {second_numerator}/{second_denominator} số gạo còn lại. Tính tỉ số số gạo bán ngày thứ ba và ngày thứ nhất.",
            f"Kho có {total} kg hàng. Lần đầu xuất {first_numerator}/{first_denominator} toàn bộ; lần hai xuất {second_numerator}/{second_denominator} phần còn lại; lần ba xuất hết. Hãy tìm tỉ số lượng xuất lần ba so với lần đầu.",
            f"Một kho có {total} kg ngũ cốc. Ngày 1 bán {first_numerator}/{first_denominator} toàn bộ, ngày 2 bán {second_numerator}/{second_denominator} phần còn lại, ngày 3 bán hết. Tính tỉ số lượng bán ngày 3 và ngày 1.",
        ][variant]
        data = [
            quantity("mass", total, "Toàn bộ ban đầu", "kg"),
            quantity("numerator", first_numerator, "Tử số phần lần thứ nhất"),
            quantity("denominator", first_denominator, "Mẫu số phần lần thứ nhất"),
            quantity("addend_numerator", second_numerator, "Tử số phần lần thứ hai"),
            quantity("addend_denominator", second_denominator, "Mẫu số phần lần thứ hai"),
        ]
        return stem, document(
            stem,
            7,
            "ratio",
            family,
            data,
            [unknown("result", "ratio", "Tỉ số lần thứ ba và lần thứ nhất")],
            "word_problem",
        )

    if family == "sequential_fraction_remainder_quantity":
        total_m2 = 300 + 15 * rng.randint(0, 400)
        large_dam2, extra_m2 = divmod(total_m2, 100)
        if extra_m2 == 0:
            total_m2 += 15
            large_dam2, extra_m2 = divmod(total_m2, 100)
        stems = [
            f"Một khu đất rộng {large_dam2}dam2 {extra_m2}m2, người ta sử dụng 2/5 diện tích để làm nhà và 1/3 diện tích đất còn lại để trồng hoa. Phần đất cuối cùng làm chuồng trại. Tính diện tích đất làm chuồng trại.",
            f"Khu vườn có diện tích {large_dam2} dam² {extra_m2} m². Dùng 2/5 toàn bộ để trồng cây, rồi dùng 1/3 phần còn lại làm lối đi. Diện tích cuối cùng dành để trồng hoa là bao nhiêu?",
            f"Một nông trại rộng {large_dam2}dam2 {extra_m2}m2. Lần đầu dùng 2/5 diện tích, lần sau dùng 1/3 diện tích còn lại; phần cuối cùng làm khu chăn nuôi. Tính diện tích khu chăn nuôi.",
        ]
        stem = stems[variant]
        data = [
            quantity("area", large_dam2 * 100, f"{large_dam2} dam² = {large_dam2 * 100} m²", "m2"),
            quantity("area", extra_m2, f"{extra_m2} m²", "m2"),
            quantity("numerator", 2, "Tử số phần dùng lần thứ nhất"),
            quantity("denominator", 5, "Mẫu số phần dùng lần thứ nhất"),
            quantity("addend_numerator", 1, "Tử số phần dùng từ phần còn lại"),
            quantity("addend_denominator", 3, "Mẫu số phần dùng từ phần còn lại"),
        ]
        data[0]["evidence"] = {"confidence": 1.0, "status": "inferred"}
        return stem, document(
            stem,
            6,
            "ratio",
            family,
            data,
            [unknown("result", "area", "Diện tích phần cuối cùng", "m2")],
            "word_problem",
        )

    if family == "linear_equation":
        coefficient, constant, solution = rng.randint(2, 9), rng.randint(-8, 12), rng.randint(1, 12)
        result = coefficient * solution + constant
        sign = "+" if constant >= 0 else "−"
        stem = [f"Giải phương trình {coefficient}x {sign} {abs(constant)} = {result}.", f"Dùng cân thăng bằng tìm x: {coefficient}x {sign} {abs(constant)} = {result}.", f"Tìm nghiệm của {coefficient}x {sign} {abs(constant)} = {result}."][variant]
        data = [quantity("coefficient", coefficient, "Hệ số của x"), quantity("constant", constant, "Hằng số ở vế trái"), quantity("result", result, "Vế phải")]
        return stem, document(stem, 7, "algebra", family, data, [unknown("variable", "number", "Giá trị x")])

    if family in {"polynomial_evaluate_reorder", "polynomial_add_subtract"}:
        def polynomial_terms() -> list[tuple[int, int]]:
            exponents = rng.sample(range(0, 5), 3)
            return [(rng.choice([item for item in range(-6, 7) if item]), exponent) for exponent in exponents]

        def expression(terms: list[tuple[int, int]]) -> str:
            pieces = []
            for coefficient, exponent in terms:
                variable = "" if exponent == 0 else "x" if exponent == 1 else f"x^{exponent}"
                magnitude = "" if abs(coefficient) == 1 and variable else str(abs(coefficient))
                pieces.append(("−" if coefficient < 0 else "+", f"{magnitude}{variable}"))
            first_sign, first_body = pieces[0]
            return f"{'' if first_sign == '+' else '−'}{first_body} " + " ".join(f"{sign} {body}" for sign, body in pieces[1:])

        first = polynomial_terms()
        data = []
        for coefficient, exponent in first:
            data.extend([quantity("coefficient", coefficient, "Hệ số hạng tử"), quantity("exponent", exponent, "Bậc hạng tử")])
        if family == "polynomial_evaluate_reorder":
            x = rng.randint(-3, 4)
            data.append(quantity("x_value", x, "Giá trị x"))
            stem = [f"Sắp xếp đa thức P(x) = {expression(first)} theo bậc giảm dần rồi tính P({x}).", f"Dùng tile theo bậc để thu gọn {expression(first)} và thay x={x}.", f"Biểu diễn các hạng tử của {expression(first)}, sắp theo bậc và tính tại x={x}."][variant]
            problem_type = family
        else:
            second = polynomial_terms()
            subtract = index % 2 == 0
            for coefficient, exponent in second:
                data.extend([quantity("coefficient", coefficient, "Hệ số đa thức thứ hai"), quantity("exponent", exponent, "Bậc hạng tử đa thức thứ hai")])
            data.append(quantity("count", len(first), "Số hạng tử đa thức thứ nhất"))
            symbol = "−" if subtract else "+"
            stem = [f"Tính ({expression(first)}) {symbol} ({expression(second)}).", f"Dùng tile để {('trừ' if subtract else 'cộng')} hai đa thức {expression(first)} và {expression(second)}.", f"Xếp theo bậc rồi thu gọn ({expression(first)}) {symbol} ({expression(second)})."][variant]
            problem_type = f"{family}_{'subtraction' if subtract else 'addition'}"
        return stem, document(stem, 7, "algebra", problem_type, data, [unknown("result", "polynomial", "Đa thức kết quả")])

    if family == "linear_function":
        slope, intercept = rng.choice([item for item in range(-9, 10) if item]), rng.randint(-7, 7)
        sign = "+" if intercept >= 0 else "−"
        stem = [f"Vẽ đồ thị hàm số y = {slope}x {sign} {abs(intercept)}.", f"Lập bảng điểm rồi biểu diễn y = {slope}x {sign} {abs(intercept)} trên hệ trục.", f"Dựng tung độ gốc và hệ số góc của y = {slope}x {sign} {abs(intercept)}."][variant]
        data = [quantity("coefficient", slope, "Hệ số góc m"), quantity("constant", intercept, "Tung độ gốc b")]
        return stem, document(stem, 8, "algebra", family, data, [unknown("result", "graph", "Đồ thị hàm số")], "construction")

    if family == "coordinate_plot":
        x, y = rng.randint(-6, 6), rng.randint(-6, 6)
        stem = [f"Biểu diễn điểm A({x}; {y}) trên mặt phẳng tọa độ.", f"Đặt điểm M có hoành độ {x} và tung độ {y} lên hệ trục.", f"Dựng hai trục rồi đánh dấu P({x}; {y})."][variant]
        data = [quantity("x_value", x, "Hoành độ"), quantity("y_value", y, "Tung độ")]
        return stem, document(stem, 6, "coordinate", family, data, [unknown("result", "point_plot", "Vị trí điểm")], "construction")

    if family in {"rectangle_area", "rectangle_perimeter"}:
        length, width = rng.randint(4, 18), rng.randint(2, 12)
        if family == "rectangle_area":
            stem = [f"Hình chữ nhật dài {length} cm, rộng {width} cm. Tính diện tích.", f"Vẽ hình chữ nhật có chiều dài {length} cm và chiều rộng {width} cm rồi tìm diện tích.", f"Một khu đất chữ nhật dài {length} m, rộng {width} m. Diện tích bằng bao nhiêu?"][variant]
            unknown_kind = "area"
            unknown_label = "Diện tích"
        else:
            stem = [f"Vườn hình chữ nhật dài {length} m, rộng {width} m. Tính độ dài hàng rào bao quanh vườn.", f"Vẽ hình chữ nhật dài {length} cm, rộng {width} cm rồi tính chu vi.", f"Một sân chữ nhật có hai kích thước {length} m và {width} m. Chu vi sân là bao nhiêu?"][variant]
            unknown_kind = "length"
            unknown_label = "Chu vi"
        unit = "m" if variant == 2 else "cm"
        data = [quantity("length", length, "Chiều dài", unit), quantity("width", width, "Chiều rộng", unit)]
        unknown_unit = f"{unit}2" if family == "rectangle_area" else unit
        grade = 4 if family == "rectangle_area" else 3
        return stem, document(stem, grade, "geometry_2d", family, data, [unknown("result", unknown_kind, unknown_label, unknown_unit)], "word_problem")

    if family == "cuboid_volume":
        length, width, height = rng.randint(3, 12), rng.randint(2, 9), rng.randint(2, 8)
        stem = [f"Hình hộp chữ nhật dài {length} cm, rộng {width} cm, cao {height} cm. Tính thể tích.", f"Dựng hình hộp trên trục x-y-z với các kích thước {length} cm, {width} cm, {height} cm rồi tìm thể tích.", f"Một khối hộp có chiều dài {length} cm, chiều rộng {width} cm và chiều cao {height} cm. Thể tích là bao nhiêu?"][variant]
        data = [quantity("length", length, "Chiều dài", "cm"), quantity("width", width, "Chiều rộng", "cm"), quantity("height", height, "Chiều cao", "cm")]
        return stem, document(stem, 5, "geometry_3d", family, data, [unknown("result", "volume", "Thể tích", "cm3")], "word_problem")

    if family == "cylinder_cone_sphere_volume":
        kind = ["cylinder", "cone", "sphere"][index % 3]
        radius = rng.randint(2, 9)
        height = rng.randint(3, 14)
        names = {"cylinder": "hình trụ", "cone": "hình nón", "sphere": "hình cầu"}
        if kind == "sphere":
            stem = [f"Hình cầu có bán kính {radius} cm. Dựng các lớp tròn và tính thể tích.", f"Mô phỏng khối cầu bán kính {radius} cm rồi dùng công thức 4/3πr³.", f"Tính thể tích hình cầu bán kính {radius} cm bằng mô hình mặt cắt."][variant]
            data = [quantity("radius", radius, "Bán kính", "cm")]
        else:
            stem = [f"{names[kind].title()} có bán kính đáy {radius} cm và chiều cao {height} cm. Tính thể tích.", f"Dựng các lớp của {names[kind]} với r={radius} cm, h={height} cm rồi tính thể tích.", f"Mô phỏng {names[kind]} bán kính {radius} cm, cao {height} cm và thay vào công thức thể tích."][variant]
            data = [quantity("radius", radius, "Bán kính đáy", "cm"), quantity("height", height, "Chiều cao", "cm")]
        return stem, document(stem, 9, "geometry_3d", f"{kind}_volume", data, [unknown("volume", "volume", "Thể tích", "cm3")], "word_problem")

    if family == "binomial_expansion":
        a, b = rng.randint(2, 20), rng.randint(1, 15)
        stem = [f"Dùng mô hình diện tích để khai triển ({a} + {b})^2.", f"Chia hình vuông cạnh {a} + {b} để chứng minh hằng đẳng thức.", f"Biểu diễn ({a} + {b})^2 bằng bốn miền diện tích rồi khai triển."][variant]
        data = [quantity("constant", a, "Cạnh a"), quantity("constant", b, "Cạnh b")]
        return stem, document(stem, 8, "algebra", family, data, [unknown("result", "expanded_expression", "Biểu thức khai triển")], "proof")

    if family == "linear_inequality_one_variable":
        coefficient = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
        boundary = rng.randint(-8, 8)
        right_side = coefficient * boundary
        operator = rng.choice([">", "<", "≥", "≤"])
        stems = [
            f"Giải bất phương trình {coefficient}x {operator} {right_side}.",
            f"Biểu diễn tập nghiệm của {coefficient}x {operator} {right_side} trên trục số.",
            f"Tìm x thỏa mãn bất phương trình {coefficient}x {operator} {right_side} rồi tô miền nghiệm.",
        ]
        stem = stems[variant]
        relation = {
            "type": "solution_set",
            "participant_roles": {"coefficient": "coefficient", "constant": "constant"},
            "parameters": {"kind": "inequality", "symbol": "x", "operator": operator, "strict": operator in (">", "<")},
            "evidence": EVIDENCE,
        }
        return stem, document(
            stem, 9, "algebra", family,
            [quantity("coefficient", coefficient, "Hệ số của x"), quantity("constant", right_side, "Vế phải")],
            [unknown("variable", "solution_set", "Tập nghiệm của x")],
            relationships=[relation],
        )

    if family == "product_equation_roots":
        first_root, second_root = rng.sample(range(-9, 10), 2)
        first_constant, second_constant = -first_root, -second_root
        def factor(value: int) -> str:
            return f"(x {'+' if value >= 0 else '-'} {abs(value)})"
        stems = [
            f"Giải phương trình {factor(first_constant)}{factor(second_constant)} = 0.",
            f"Tìm tổng các nghiệm của {factor(first_constant)}{factor(second_constant)} = 0.",
            f"Dùng quy tắc tích bằng 0 cho {factor(first_constant)}{factor(second_constant)} = 0.",
        ]
        stem = stems[variant]
        relation = {
            "type": "solution_set",
            "participant_roles": {
                "first_coefficient": "coefficient[1]", "first_constant": "constant[1]",
                "second_coefficient": "coefficient[2]", "second_constant": "constant[2]",
            },
            "parameters": {"kind": "product_roots", "symbol": "x", "factors": [[1, first_constant], [1, second_constant]]},
            "evidence": EVIDENCE,
        }
        return stem, document(
            stem, 9, "algebra", family,
            [
                quantity("coefficient", 1, "Hệ số thừa số thứ nhất"),
                quantity("constant", first_constant, "Hằng số thừa số thứ nhất"),
                quantity("coefficient", 1, "Hệ số thừa số thứ hai"),
                quantity("constant", second_constant, "Hằng số thừa số thứ hai"),
            ],
            [unknown("variable", "solution_set", "Các nghiệm của x")],
            relationships=[relation],
        )

    if family == "rational_equation_domain":
        first_excluded, second_excluded = rng.sample(range(-9, 10), 2)
        first_constant, second_constant = -first_excluded, -second_excluded
        def denominator(value: int) -> str:
            return f"x {'+' if value >= 0 else '-'} {abs(value)}"
        stems = [
            f"Tìm điều kiện xác định của phương trình 1/({denominator(first_constant)}) = 2/({denominator(second_constant)}).",
            f"Điều kiện xác định của phân thức 1/({denominator(first_constant)}) + 1/({denominator(second_constant)}) là gì?",
            f"Cho các mẫu thức {denominator(first_constant)} và {denominator(second_constant)}. Tìm điều kiện xác định.",
        ]
        stem = stems[variant]
        relation = {
            "type": "solution_set",
            "participant_roles": {
                "first_coefficient": "coefficient[1]", "first_constant": "constant[1]",
                "second_coefficient": "coefficient[2]", "second_constant": "constant[2]",
            },
            "parameters": {"kind": "excluded_values", "symbol": "x", "denominators": [[1, first_constant], [1, second_constant]]},
            "evidence": EVIDENCE,
        }
        return stem, document(
            stem, 9, "algebra", family,
            [
                quantity("coefficient", 1, "Hệ số mẫu thức thứ nhất"),
                quantity("constant", first_constant, "Hằng số mẫu thức thứ nhất"),
                quantity("coefficient", 1, "Hệ số mẫu thức thứ hai"),
                quantity("constant", second_constant, "Hằng số mẫu thức thứ hai"),
            ],
            [unknown("variable", "solution_set", "Điều kiện xác định của x")],
            relationships=[relation],
        )

    if family == "angle_of_depression_distance":
        height = rng.randint(30, 250)
        angle = rng.choice([20, 25, 27, 30, 35, 40, 45])
        stems = [
            f"Đài hải đăng cao {height} m nhìn thấy tàu với góc nghiêng xuống đất {angle}°. Hỏi tàu cách chân hải đăng bao nhiêu mét?",
            f"Từ đỉnh tháp cao {height} m, góc hạ đến một chiếc xe là {angle}°. Tính khoảng cách ngang từ xe đến chân tháp.",
            f"Một người ở tòa nhà cao {height} m nhìn xuống mặt đất theo góc {angle}°. Điểm nhìn cách chân tòa nhà bao xa?",
        ]
        stem = stems[variant]
        relation = {
            "type": "trigonometric_geometry",
            "participant_roles": {"height": "height", "angle": "angle"},
            "parameters": {"kind": "angle_of_depression", "height": height, "angle": angle, "unit": "m", "landmark": "vertical_landmark"},
            "evidence": EVIDENCE,
        }
        return stem, document(
            stem, 9, "geometry_2d", family,
            [quantity("height", height, "Chiều cao điểm quan sát", "m"), quantity("angle", angle, "Góc nghiêng xuống", "degree")],
            [unknown("result", "distance", "Khoảng cách ngang", "m")],
            "word_problem", relationships=[relation],
        )

    if family == "oblique_triangle_altitude_solution":
        height = rng.randint(3, 16)
        first_angle = rng.randint(35, 75)
        second_angle = rng.randint(30, 80)
        if first_angle + second_angle >= 150:
            second_angle = 145 - first_angle
        stems = [
            f"Cho tam giác ABC có đường cao AH = {height} cm, góc B = {first_angle}°, góc C = {second_angle}°. Tính độ dài các cạnh.",
            f"Tam giác ABC có AH = {height} cm vuông góc BC, góc B bằng {first_angle}° và góc C bằng {second_angle}°. Giải tam giác.",
            f"Hạ đường cao AH của tam giác ABC, biết AH = {height} cm, B = {first_angle}°, C = {second_angle}°. Tìm AB, AC, BC.",
        ]
        stem = stems[variant]
        relation = {
            "type": "trigonometric_geometry",
            "participant_roles": {"height": "height", "first_angle": "angle[1]", "second_angle": "angle[2]"},
            "parameters": {"kind": "oblique_triangle_altitude", "vertices": "ABC", "apex": "A", "foot": "H", "height": height, "angles": {"B": first_angle, "C": second_angle}, "unit": "cm"},
            "evidence": EVIDENCE,
        }
        return stem, document(
            stem, 9, "geometry_2d", family,
            [quantity("height", height, "Đường cao AH", "cm"), quantity("angle", first_angle, "Góc B", "degree"), quantity("angle", second_angle, "Góc C", "degree")],
            [unknown("result", "length", "Cạnh AB", "cm"), unknown("result", "length", "Cạnh AC", "cm"), unknown("result", "length", "Cạnh BC", "cm")],
            "word_problem", relationships=[relation],
        )

    if family == "parallelogram_perpendicular_diagonal_area":
        # Keep enough independent numeric combinations for the 80-item train
        # split.  The former 6 x 7 pool capped this family at 42 unique stems.
        side = rng.choice([value / 2 for value in range(4, 25)])
        angle = rng.choice(list(range(20, 75, 5)))
        stems = [
            f"Cho hình bình hành ABCD có AC ⟂ AD, AD = {str(side).replace('.', ',')} cm, góc D = {angle}°. Tính diện tích.",
            f"Hình bình hành ABCD có đường chéo AC vuông góc cạnh AD = {str(side).replace('.', ',')} cm và góc D bằng {angle}°. Tìm diện tích.",
            f"Dựng ABCD với AC ⟂ AD, AD = {str(side).replace('.', ',')} cm, góc D = {angle}° rồi tính diện tích hình bình hành.",
        ]
        stem = stems[variant]
        relation = {
            "type": "trigonometric_geometry",
            "participant_roles": {"side": "length", "angle": "angle"},
            "parameters": {"kind": "parallelogram_perpendicular_diagonal", "vertices": "ABCD", "diagonal": "AC", "side": "AD", "side_length": side, "angle_vertex": "D", "angle": angle, "unit": "cm"},
            "evidence": EVIDENCE,
        }
        return stem, document(
            stem, 9, "geometry_2d", family,
            [quantity("length", side, "Cạnh AD", "cm"), quantity("angle", angle, "Góc D", "degree")],
            [unknown("result", "area", "Diện tích hình bình hành", "cm2")],
            "word_problem", relationships=[relation],
        )

    if family == "quadratic_surface_three_variables":
        squared_coefficient = rng.choice([-3, -2, -1, 1, 2, 3])
        y_coefficient = rng.choice([-6, -5, -4, -2, 2, 4, 5, 6])
        z_coefficient = rng.choice([-1, 1])
        right_side = rng.randint(-5, 5)
        terms = f"{squared_coefficient}x² {'+' if y_coefficient > 0 else '-'} {abs(y_coefficient)}y {'+' if z_coefficient > 0 else '-'} z = {right_side}"
        stems = [f"Biểu diễn mặt nghiệm {terms} trên hệ trục Oxyz.", f"Dựng mặt cong của phương trình {terms}.", f"Vẽ các lát parabol của {terms} rồi nối thành mặt nghiệm."]
        stem = stems[variant]
        relation = {
            "type": "quadratic_surface",
            "participant_roles": {"squared": "coefficient[1]", "y": "coefficient[2]", "z": "coefficient[3]", "right_side": "constant"},
            "parameters": {"squared_symbol": "x", "squared_coefficient": squared_coefficient, "linear_coefficients": {"y": y_coefficient, "z": z_coefficient}, "right_side": right_side, "output_symbol": "z", "coordinate_system": "Oxyz"},
            "evidence": EVIDENCE,
        }
        return stem, document(
            stem, 9, "geometry_3d", family,
            [quantity("coefficient", squared_coefficient, "Hệ số x²"), quantity("coefficient", y_coefficient, "Hệ số y"), quantity("coefficient", z_coefficient, "Hệ số z"), quantity("constant", right_side, "Vế phải")],
            [unknown("result", "quadratic_surface", "Mặt cong nghiệm")],
            "construction", relationships=[relation],
        )

    if family == "distance_speed_time":
        speed, duration = rng.randint(3, 12), rng.randint(1, 5)
        distance = speed * duration
        hour, minute = rng.randint(6, 15), rng.choice([0, 15, 30, 45])
        start = f"{hour:02d}:{minute:02d}"
        stem = [f"Lan đi {distance} km với vận tốc {speed} km/h, bắt đầu lúc {start}. Hỏi chuyến đi kéo dài bao lâu?", f"Một xe xuất phát {start}, đi quãng đường {distance} km với vận tốc {speed} km/h. Tìm thời gian đi.", f"Mô phỏng hành trình dài {distance} km từ {start} với tốc độ {speed} km/h và xác định thời lượng."][variant]
        data = [quantity("distance", distance, "Quãng đường", "km"), quantity("speed", speed, "Vận tốc", "km/h")]
        return stem, document(stem, 5, "motion", family, data, [unknown("duration", "duration", "Thời gian đi", "hour")], "word_problem", entities=[{"role": "moving_entity", "type": "person", "label": "Lan", "evidence": EVIDENCE}], start_time=start)

    raise ValueError(f"Unknown family: {family}")


def render_problem(stem: str, destination: Path, rng: random.Random) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    width = 1200
    font_size = rng.randint(34, 42)
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    header_font = ImageFont.truetype(str(FONT_PATH), 24)
    wrapped = textwrap.wrap(stem, width=max(34, int(1024 / font_size * 1.7)))
    # Long word problems and true/false statements must remain fully visible.
    # The previous fixed 280 px canvas silently clipped the bottom lines, which
    # produced schema-valid targets paired with incomplete training images.
    line_height = font_size + 15
    height = max(280, 88 + len(wrapped) * line_height + 34)
    background = rng.choice([(255, 255, 255), (250, 248, 241), (245, 249, 255)])
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    for y in range(34, height, 34):
        draw.line((0, y, width, y), fill=(232, 236, 240), width=1)
    draw.text((42, 22), rng.choice(["Bài 1", "Câu 1", "Math Lab"]), font=header_font, fill=(82, 92, 105))
    draw.multiline_text((42, 72), "\n".join(wrapped), font=font, fill=(20, 28, 38), spacing=15)
    image.save(destination, optimize=True)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-per-family", type=int, default=80)
    parser.add_argument("--validation-per-family", type=int, default=12)
    parser.add_argument("--test-per-family", type=int, default=12)
    parser.add_argument("--seed", type=int, default=260826)
    args = parser.parse_args()

    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    families = [
        "addition", "subtraction", "multiplication_grouping", "division_grouping",
        "fraction_addition", "fraction_subtraction", "fraction_multiplication",
        "fraction_equivalence", "fraction_power",
        "ratio_from_known_value", "ratio_total_parts",
        "proportional_system_two_variables", "arithmetic_mean",
        "multi_step_arithmetic_word", "map_scale",
        "sequential_fraction_remainder_ratio",
        "sequential_fraction_remainder_quantity",
        "work_rate_with_variable_people",
        "linear_equation", "compound_linear_equation", "linear_function",
        "linear_inequality_one_variable", "product_equation_roots",
        "rational_equation_domain", "quadratic_surface_three_variables",
        "mixed_rational_arithmetic_percent", "discount_tax_percentage",
        "two_item_discount_system",
        "multi_segment_equal_distance_motion", "time_calendar_duration",
        "algebraic_expression_modeling", "triangle_congruence_centroid_proof",
        "triangle_similarity_metric_relation", "word_equation_rectangle",
        "right_triangle_solution",
        "angle_of_depression_distance", "oblique_triangle_altitude_solution",
        "parallelogram_perpendicular_diagonal_area",
        "coordinate_plot", "rectangle_area", "rectangle_perimeter", "cuboid_volume",
        "binomial_expansion", "distance_speed_time",
        "place_value_read_write", "decimal_read_write",
        "column_arithmetic_regrouping", "decimal_arithmetic",
        "measurement_conversion_comparison", "picture_bar_chart_reading",
        "fraction_division", "quadratic_function_graph", "quadratic_equation_vieta",
        "statistics_probability_from_chart", "triangle_area",
        "number_ordering_rounding",
        "circle_radius_diameter", "circle_area", "circle_tangent_cyclic_proof",
        "divisibility_common_multiple",
        "rhombus_parallelogram_area_properties",
        "ray_segment_midpoint", "angle_bisector",
        "experimental_probability",
        "cylinder_cone_sphere_volume",
        "percentage_part_whole",
        "polynomial_evaluate_reorder", "polynomial_add_subtract",
        "signed_decimal_fraction_ordering",
        "missing_number_equation",
        "shape_recognition_counting_pattern",
    ]
    split_counts = {
        "train": args.train_per_family,
        "validation": args.validation_per_family,
        "test": args.test_per_family,
    }
    manifest = {"seed": args.seed, "families": families, "splits": {}, "modalities": ["text", "image"]}
    for split, count in split_counts.items():
        records: list[dict] = []
        seen: set[str] = set()
        rng = random.Random(args.seed + {"train": 0, "validation": 10_000, "test": 20_000}[split])
        for family in families:
            made = 0
            attempt = 0
            while made < count:
                attempt += 1
                if attempt > max(20_000, count * 500):
                    raise RuntimeError(
                        f"Không tạo đủ stem duy nhất cho family={family}, split={split}: "
                        f"{made}/{count} sau {attempt - 1} lần thử"
                    )
                stem, target = build_case(family, attempt, rng, split)
                if stem in seen:
                    continue
                seen.add(stem)
                target_text = json.dumps(target, ensure_ascii=False, separators=(",", ":"))
                sample_id = f"{split}-{family}-{made:04d}"
                image_rel = Path("images") / split / f"{sample_id}.png"
                render_problem(stem, OUTPUT_ROOT / image_rel, rng)
                records.extend([
                    {
                        "id": f"{sample_id}-text",
                        "conversations": [
                            {"from": "human", "value": f"{prompt}\n\nNGUỒN VĂN BẢN:\n{stem}"},
                            {"from": "gpt", "value": target_text},
                        ],
                    },
                    {
                        "id": f"{sample_id}-image",
                        "image": image_rel.as_posix(),
                        "conversations": [
                            {"from": "human", "value": f"<image>\n{prompt}"},
                            {"from": "gpt", "value": target_text},
                        ],
                    },
                ])
                made += 1
        output = OUTPUT_ROOT / f"math_scene_{split}.jsonl"
        write_jsonl(output, records)
        manifest["splits"][split] = {"semantic_cases": len(records) // 2, "records": len(records), "path": output.relative_to(OUTPUT_ROOT).as_posix()}
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
