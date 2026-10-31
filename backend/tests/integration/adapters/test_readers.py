from questionary_extractor.adapters.readers import read_pdf


def read_example_pdf(examples_dir, name):
    return read_pdf((examples_dir / name).read_bytes())


def test_pdf_table_header_cells_spanning_lines_stay_together(examples_dir):
    text = read_example_pdf(examples_dir, "01_mini-ipip_big-five_en.pdf")

    assert "3 Neither Accurate Nor Inaccurate" in text


def test_pdf_table_rows_appear_once(examples_dir):
    text = read_example_pdf(examples_dir, "01_mini-ipip_big-five_en.pdf")

    assert "1 | Am the life of the party." in text
    assert text.count("Am the life of the party.") == 1


def test_pdf_answer_key_keeps_question_and_answer_on_one_row(examples_dir):
    lines = read_example_pdf(examples_dir, "04_razonamiento-logico_es.pdf").splitlines()

    assert "11 | 0,05 € (5 céntimos)" in lines
    assert "13 | 47 días" in lines


def test_pdf_text_outside_tables_is_kept(examples_dir):
    text = read_example_pdf(examples_dir, "04_razonamiento-logico_es.pdf")

    assert "¿Qué número continúa la serie? 3, 6, 12, 24, …" in text
    assert "Clave de respuestas" in text
