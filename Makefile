.PHONY: ui cli interactive

# Inicia la interfaz web de Streamlit
ui:
	@echo "📡 Iniciando la UI de Streamlit..."
	cd cli && uv run streamlit_app.py

# Inicia el modo interactivo del CLI
interactive:
	@echo "🕹️  Iniciando modo interactivo..."
	cd cli && uv run g5500_cli.py interactive

# Inicia la ayuda del CLI principal
cli:
	cd cli && uv run g5500_cli.py --help
