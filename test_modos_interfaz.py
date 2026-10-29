import ast
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from modos_app import (
    TIPO_AREA_DIBUJADA,
    TIPO_AREA_SUBCUENCA,
    aplicar_limite_cuenca,
    area_debe_recortarse_a_cuenca,
)


class GeometriaPrueba:
    def __init__(self):
        self.intersecciones = []

    def intersection(self, otra, tolerancia):
        self.intersecciones.append((otra, tolerancia))
        return "geometria-recortada"


class ModosInterfazTests(unittest.TestCase):
    def test_aplicacion_importa_la_regla_de_recorte(self):
        arbol = ast.parse(
            Path("app_experiencia.py").read_text(encoding="utf-8")
        )
        importados = {
            alias.name
            for nodo in arbol.body
            if isinstance(nodo, ast.ImportFrom) and nodo.module == "modos_app"
            for alias in nodo.names
        }

        self.assertIn("area_debe_recortarse_a_cuenca", importados)

    def test_la_pantalla_inicial_ofrece_tres_analisis_separados(self):
        app = AppTest.from_file("app.py", default_timeout=30).run()

        self.assertFalse(app.exception)
        self.assertEqual(
            [boton.label for boton in app.button if boton.label.startswith("Elegir")],
            [
                "Elegir preevaluación territorial",
                "Elegir corredores y conectividad",
                "Elegir preevaluación integral",
            ],
        )

    def test_navegacion_explica_objetivo_y_metodo_sin_iniciar_el_motor(self):
        app = AppTest.from_file("app.py", default_timeout=30).run()

        self.assertEqual(
            app.segmented_control[0].options,
            ["Mapa", "Metodología y ayuda", "Acerca del visor"],
        )

        app.segmented_control[0].set_value("Metodología y ayuda").run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any(
                "Cómo se construye la preevaluación" in bloque.value
                for bloque in app.markdown
            )
        )
        self.assertTrue(any(boton.label == "Abrir el mapa" for boton in app.button))

        app.segmented_control[0].set_value("Acerca del visor").run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any("Qué problema ayuda a resolver" in bloque.value for bloque in app.markdown)
        )
        self.assertTrue(any(boton.label == "Abrir el mapa" for boton in app.button))

    def test_la_navegacion_principal_permanece_antes_del_selector_de_enfoque(self):
        codigo = Path("app.py").read_text(encoding="utf-8")

        self.assertNotIn('SECCION_ANALISIS = "Análisis"', codigo)
        self.assertIn('st.segmented_control(', codigo)
        bloque_navegacion = codigo.index('seccion_tablero = mostrar_navegacion()')
        bloque_modo = codigo.index('if modo_analisis is None:')
        bloque_aplicacion = codigo.index('APLICACION_ACTIVA =', bloque_modo)

        self.assertLess(bloque_navegacion, bloque_modo)
        self.assertLess(bloque_modo, bloque_aplicacion)

    def test_la_portada_sigue_el_modelo_del_portal(self):
        app = AppTest.from_file("app.py", default_timeout=30).run()

        self.assertFalse(app.exception)
        bloques = " ".join(bloque.value for bloque in app.markdown)
        for texto in ("hero-cut", "class=\"meta\"", "class=\"figs\"", "Módulo 1", "class=\"foot\""):
            self.assertIn(texto, bloques)
        self.assertIn("Cómo funciona", [boton.label for boton in app.button])

    def test_el_analisis_se_presenta_como_tablero_cartografico(self):
        codigo = Path("app_experiencia.py").read_text(encoding="utf-8")

        self.assertIn("Evidencia cartográfica", codigo)
        self.assertIn("Centro del análisis", codigo)
        self.assertIn("mapa-cabecera", codigo)
        self.assertIn("Resultado de la preevaluación", codigo)
        self.assertIn("Estadísticas del área", codigo)
        self.assertIn("Gráfica vinculada al mapa", codigo)
        self.assertIn("mostrar_grafica_contextual_dashboard", codigo)
        self.assertIn("resolver_capa_contextual", codigo)
        self.assertIn("crear_grafica_serie_barras", codigo)
        self.assertIn("mostrar_graficas_dashboard", codigo)
        self.assertIn("crear_grafica_barras_color", codigo)
        self.assertIn("st.altair_chart", codigo)
        self.assertNotIn("st.line_chart", codigo)
        self.assertNotIn('"tipo": "lineas"', codigo)
        self.assertIn("Deforestación por año", codigo)
        self.assertIn("Hectáreas clasificadas anualmente como deforestación", codigo)
        self.assertIn("COLORES_FUENTES", codigo)
        self.assertIn('"JRC TMF": "#1F8A70"', codigo)
        self.assertIn('"Hansen GFC": "#E76F51"', codigo)
        self.assertIn('"ESRI LULC": "#3A7CA5"', codigo)
        self.assertIn('"GEDI": "#7A5195"', codigo)
        self.assertIn('"NDVI": "#9BBF30"', codigo)
        self.assertIn('text=alt.Text("Etiqueta:N")', codigo)
        self.assertIn("Aporte de las fuentes al índice", codigo)
        self.assertIn("Superficie con indicios", codigo)
        self.assertIn("Relación entre fragmentos", codigo)
        self.assertIn("Resultados completos", codigo)
        self.assertIn("Crear análisis", codigo)
        self.assertIn("Detalle y descargas", codigo)
        self.assertIn("Abrir detalle completo y descargas", codigo)
        self.assertIn("Volver al mapa", codigo)
        self.assertIn('st.session_state["mostrar_resultados"] = False', codigo)
        self.assertIn(
            "El resultado aparece en la columna derecha sin ocultar el mapa",
            codigo,
        )
        self.assertIn("Evolución por fuente", codigo)
        self.assertIn("JRC Tropical Moist Forest", codigo)
        self.assertIn("Hansen Global Forest Change", codigo)
        self.assertIn("ESRI Land Use / Land Cover", codigo)
        self.assertIn("Sentinel-2 · NDVI", codigo)
        self.assertIn("GEDI · altura del dosel", codigo)
        self.assertIn('if seccion_tablero == "Análisis":', codigo)
        self.assertIn('["Resumen"]', codigo)
        self.assertNotIn("mostrar_flujo(2)", codigo)
        self.assertNotIn("Ver detalles del análisis · opcional", codigo)

    def test_modelo_html_conserva_el_analisis_y_declara_su_identidad(self):
        portada = Path("app.py").read_text(encoding="utf-8")
        visor = Path("app_experiencia.py").read_text(encoding="utf-8")

        self.assertIn("mostrar_navegacion", portada)
        self.assertIn("mostrar_heroe", portada)
        self.assertIn("Visor CHCP", portada)
        self.assertIn("Google Earth Engine", portada)
        self.assertIn("WGS 84 · EPSG:4326", portada)
        self.assertIn("#0a4393", portada.lower())
        self.assertIn("#77cc09", portada.lower())
        self.assertIn('APP_VERSION = "UX-5.0.0-PORTAL-MODELO"', visor)
        self.assertIn("st.columns([2.55, 1]", visor)
        self.assertNotIn('st.markdown("### Visor cartográfico")', visor)
        for fuente in ("JRC", "Hansen", "ESRI", "GEDI", "NDVI"):
            self.assertIn(fuente, visor)

    def test_subcuenca_se_recorta_a_la_cuenca(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            TIPO_AREA_SUBCUENCA,
            geometria,
            "limite-cuenca",
        )

        self.assertEqual(resultado, "geometria-recortada")
        self.assertEqual(geometria.intersecciones, [("limite-cuenca", 10)])
        self.assertTrue(area_debe_recortarse_a_cuenca(TIPO_AREA_SUBCUENCA))

    def test_poligono_dibujado_se_recorta_a_la_cuenca(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            TIPO_AREA_DIBUJADA,
            geometria,
            "limite-cuenca",
        )

        self.assertEqual(resultado, "geometria-recortada")
        self.assertEqual(geometria.intersecciones, [("limite-cuenca", 10)])
        self.assertTrue(area_debe_recortarse_a_cuenca(TIPO_AREA_DIBUJADA))

    def test_finca_se_recorta_a_la_cuenca(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            "Finca de monitoreo",
            geometria,
            "limite-cuenca",
        )

        self.assertEqual(resultado, "geometria-recortada")
        self.assertTrue(area_debe_recortarse_a_cuenca("Finca de monitoreo"))

    def test_cuenca_completa_no_se_recorta_contra_si_misma(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            "Toda la cuenca",
            geometria,
            "limite-cuenca",
        )

        self.assertIs(resultado, geometria)
        self.assertFalse(geometria.intersecciones)
        self.assertFalse(area_debe_recortarse_a_cuenca("Toda la cuenca"))


if __name__ == "__main__":
    unittest.main()
