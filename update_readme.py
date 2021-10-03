import json
import pathlib
import re
import sys

from mdutils.mdutils import MdUtils

root = pathlib.Path(__file__).parent.resolve()

mdFile = MdUtils(file_name="README")
index_re = re.compile(
    r"<!\-\- table starts \-\->.*<!\-\- table ends \-\->",
    re.DOTALL,
)


def table_datasets():
    with open("datasets.json") as json_file:
        datasets = json.load(json_file)

    dataset_table = [
        "Dataset",
        "Source",
        "Date Range",
        "Updated",
        "Download",
        "Preview",
    ]
    columns = len(dataset_table)

    link = mdFile.new_inline_link
    for ds in datasets:
        dataset_table.extend(
            [
                link(
                    link=ds["dataset_detail"],
                    text=ds["name"],
                ),
                ds["source"],
                ds["date_range"],
                ds["last_updated"],
                link(
                    link=ds["link_csv"],
                    text="csv",
                    align="center",
                ),
                link(
                    link=ds["link_preview"],
                    text="preview",
                    align="center",
                ),
            ]
        )

    mdFile.new_table(
        columns=columns,
        rows=len(datasets) + 1,
        text=dataset_table,
        text_align="left",
    )


if __name__ == "__main__":
    table_datasets()
    table = mdFile.file_data_text

    index = ["<!-- table starts -->"]
    index.append(table)
    index.append("<!-- table ends -->")

    if "--rewrite" in sys.argv:
        readme = root / "README.md"
        index_txt = "".join(index).strip()
        readme_contents = readme.open().read()
        rewritten = index_re.sub(index_txt, readme_contents)
        readme.open("w").write(rewritten)
    else:
        print("".join(index))
