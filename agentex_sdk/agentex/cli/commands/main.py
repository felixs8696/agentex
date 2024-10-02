from typing import Optional

import typer

app = typer.Typer(
    context_settings=dict(help_option_names=["-h", "--help"], max_content_width=800),
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def register_action(
    build_manifest_path: Optional[str] = typer.Option(
        None, help="Path to the build manifest you want to use"
    )
):




if __name__ == "__main__":
    app()
