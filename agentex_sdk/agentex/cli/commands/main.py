import typer

app = typer.Typer(
    context_settings=dict(help_option_names=["-h", "--help"], max_content_width=800),
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
    add_completion=False,
)


@app.command()
def echo(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()
