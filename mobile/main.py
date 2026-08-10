import json
import os
import tempfile
import colorsys
import flet as ft
import tinytuya

# --- ARCHIVO DE PERSISTENCIA (Ruta segura compatible con Android y Windows) ---
PRESETS_FILE = os.path.join(tempfile.gettempdir(), "lumina_presets.json")

DEFAULT_PRESETS = [
    [255, 59, 48, "#FF3B30"],
    [50, 173, 230, "#32ADE6"],
    [52, 199, 89, "#34C759"],
    [175, 82, 222, "#AF52DE"],
    [255, 149, 0, "#FF9500"],
]

def load_saved_presets():
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print("Error leyendo presets:", e)
    return DEFAULT_PRESETS

def save_presets_to_file(presets):
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Fuerza la escritura física en disco
    except Exception as e:
        print("Error guardando presets:", e)

# Credenciales confirmadas
DEVICE_ID = "ebc0f9dafaa662ccd90tr4"
IP_ADDRESS = "192.168.1.33"  
LOCAL_KEY = "-{iM9r9sBJ/*LF7E"

try:
    luz = tinytuya.BulbDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
    luz.set_version(3.5)
    luz.set_socketPersistent(True) 
except Exception as e:
    print("Error al inicializar la lámpara:", e)

def main(page: ft.Page):
    page.title = "Lumina Studio"
    page.theme_mode = "dark"
    page.bgcolor = "#0f0f13"  
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"
    page.padding = 15

    # --- ESTADO INTERNO ---
    state = {
        "is_on": True,
        "mode": "colour", 
        "brightness": 70, 
        "temp": 50,       
        "base_rgb": (112, 66, 157), 
        "hex": "#70429D",
        "hsv_str": "D 270 S 57 V 61",
        "presets": load_saved_presets()
    }

    # --- FUNCIONES DE COMUNICACIÓN DIRECTA (DPs) ---
    def sync_lamp():
        if not state["is_on"]:
            return 

        try:
            if state["mode"] == "colour":
                r, g, b = state["base_rgb"]
                h, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                
                v = max(0.01, state["brightness"] / 100.0)
                
                tuya_h = int(h * 360)
                tuya_s = int(s * 1000)
                tuya_v = int(v * 1000)
                hex_hsv = f"{tuya_h:04x}{tuya_s:04x}{tuya_v:04x}"
                
                luz.set_multiple_values({
                    '21': 'colour',
                    '24': hex_hsv
                })
            else:
                tuya_br = max(10, int(state["brightness"] * 10))
                tuya_temp = max(0, int(state["temp"] * 10))      
                
                luz.set_multiple_values({
                    '21': 'white',
                    '22': tuya_br,
                    '23': tuya_temp
                })
        except Exception as ex:
            print("Error al sincronizar:", ex)

    def toggle_power(e):
        state["is_on"] = e.control.value
        try:
            luz.set_value('20', state["is_on"]) 
            if state["is_on"]:
                sync_lamp()
        except:
            pass
        page.update()

    def update_color_texts(r, g, b, hex_code):
        state["base_rgb"] = (r, g, b)
        state["hex"] = hex_code.upper()
        h, s, _ = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        v = state["brightness"] / 100.0
        state["hsv_str"] = f"D {int(h*360)} S {int(s*100)} V {int(v*100)}"
        
        hex_text.value = state["hex"]
        hsv_text.value = state["hsv_str"]
        color_preview.bgcolor = state["hex"]

    def set_color(r, g, b, hex_code):
        def on_click(e):
            state["mode"] = "colour"
            update_color_texts(r, g, b, hex_code)
            
            h, _, _ = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            hue_slider.value = int(h * 360)

            tab_rgb_btn.bgcolor = "#7c3aed"
            tab_white_btn.bgcolor = "#22222f"
            color_panel.visible = True
            white_panel.visible = False
            
            sync_lamp()
            page.update()
        return on_click

    def set_white_mode(e):
        state["mode"] = "white"
        
        tab_white_btn.bgcolor = "#7c3aed"
        tab_rgb_btn.bgcolor = "#22222f"
        white_panel.visible = True
        color_panel.visible = False
        
        sync_lamp()
        page.update()

    def on_hue_change(e):
        hue_deg = float(e.control.value)
        hue_frac = hue_deg / 360.0
        r, g, b = colorsys.hsv_to_rgb(hue_frac, 1.0, 1.0)
        r_int, g_int, b_int = int(r * 255), int(g * 255), int(b * 255)
        hex_code = f"#{r_int:02x}{g_int:02x}{b_int:02x}".upper()

        state["mode"] = "colour"
        update_color_texts(r_int, g_int, b_int, hex_code)
        page.update()

    def on_hue_change_end(e):
        sync_lamp()

    def on_brightness_change(e):
        state["brightness"] = int(e.control.value)
        br_text.value = f"{state['brightness']}%"
        r, g, b = state["base_rgb"]
        update_color_texts(r, g, b, state["hex"])
        sync_lamp()
        page.update()

    def on_temp_change(e):
        state["temp"] = int(e.control.value)
        sync_lamp()
        page.update()

    # --- INTERFAZ GRÁFICA ---
    
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("LUMINA STUDIO", size=10, weight="bold", color="#7c3aed"),
                        ft.Text("Control Iluminación", size=18, weight="bold", color="#ffffff"),
                    ], spacing=2
                ),
                ft.Switch(value=True, active_color="#ffffff", active_track_color="#7c3aed", on_change=toggle_power)
            ],
            alignment="spaceBetween"
        ),
        bgcolor="#1a1a24", padding=15, border_radius=15
    )

    tab_rgb_btn = ft.Container(
        content=ft.Text("COLOR RGB", size=12, weight="bold", color="#ffffff", text_align="center"),
        bgcolor="#7c3aed", padding=12, border_radius=8, expand=True, on_click=lambda e: set_color(112, 66, 157, "#70429D")(e)
    )
    tab_white_btn = ft.Container(
        content=ft.Text("BLANCO KELVIN", size=12, weight="bold", color="#ffffff", text_align="center"),
        bgcolor="#22222f", padding=12, border_radius=8, expand=True, on_click=set_white_mode
    )
    tabs_row = ft.Row(controls=[tab_rgb_btn, tab_white_btn], spacing=10)

    # --- INDICADOR DE COLOR INTEGRADO ---
    hex_text = ft.Text("#70429D", size=14, weight="bold", color="#ffffff")
    hsv_text = ft.Text("D 270 S 57 V 61", size=11, weight="bold", color="#a0a0b0")

    color_preview = ft.Container(
        height=42, 
        border_radius=10, 
        bgcolor="#70429D",
        padding=ft.Padding(15, 0, 15, 0),
        content=ft.Row(
            controls=[
                ft.Text("COLOR ACTIVO", size=11, weight="bold", color="#ffffff"),
                hex_text
            ],
            alignment="spaceBetween"
        )
    )

    # --- SLIDER SUPERPUESTO EN LA BARRA DE ARCOÍRIS ---
    rainbow_bar = ft.Container(
        height=14, border_radius=7,
        margin=ft.Margin(0, 14, 0, 0),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
            colors=[
                "#ff0000", "#ffff00", "#00ff00", 
                "#00ffff", "#0000ff", "#ff00ff", "#ff0000"
            ]
        )
    )

    hue_slider = ft.Slider(
        min=0, max=360, divisions=360, value=270,
        active_color="transparent", inactive_color="transparent",
        thumb_color="#ffffff",
        on_change=on_hue_change,
        on_change_end=on_hue_change_end
    )

    rainbow_slider_stack = ft.Stack(
        controls=[
            rainbow_bar,
            hue_slider
        ]
    )

    # --- GESTIÓN Y PERSISTENCIA DE PRESETS ---
    presets_row = ft.Row(controls=[], spacing=10, wrap=True)

    def delete_preset(hex_code):
        state["presets"] = [p for p in state["presets"] if p[3] != hex_code]
        save_presets_to_file(state["presets"])
        refresh_presets()
        page.update()

    def color_circle(r, g, b, hex_code):
        circle = ft.Container(
            width=32, height=32, bgcolor=hex_code, border_radius=16,
            tooltip=f"{hex_code}\n(Clic derecho / mantener para borrar)"
        )
        return ft.GestureDetector(
            content=circle,
            on_tap=set_color(r, g, b, hex_code),
            on_secondary_tap=lambda e: delete_preset(hex_code),
            on_long_press_start=lambda e: delete_preset(hex_code)
        )

    def add_current_preset(e):
        r, g, b = state["base_rgb"]
        hex_code = state["hex"]
        if not any(p[3] == hex_code for p in state["presets"]):
            state["presets"].append([r, g, b, hex_code])
            save_presets_to_file(state["presets"])
            refresh_presets()
            page.update()

    def refresh_presets():
        controls = []
        for r, g, b, hex_code in state["presets"]:
            controls.append(color_circle(r, g, b, hex_code))
        
        controls.append(
            ft.Container(
                width=32, height=32, bgcolor="#2a2a38", border_radius=16,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon("add", size=16, color="#ffffff"),
                on_click=add_current_preset,
                tooltip="Guardar color actual"
            )
        )
        presets_row.controls = controls

    refresh_presets()

    color_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("SELECCIÓN DE TONO", size=10, weight="bold", color="#a0a0b0"),
                color_preview,
                rainbow_slider_stack,
                ft.Row([ft.Text("Espectro HSV", size=10, color="#a0a0b0"), hsv_text], alignment="spaceBetween"),
                ft.Container(height=15),
                ft.Row([
                    ft.Text("MIS PRESETS", size=10, weight="bold", color="#a0a0b0"),
                    ft.Text("(Mantener/Clic derecho para borrar)", size=9, color="#606070")
                ], alignment="spaceBetween"),
                presets_row
            ]
        ),
        bgcolor="#1a1a24", padding=20, border_radius=15, visible=True
    )

    # --- PANEL BLANCO ---
    temp_slider = ft.Slider(
        min=0, max=100, divisions=100, value=50, 
        active_color="#fbbf24", inactive_color="#333344",
        on_change_end=on_temp_change
    )
    
    white_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("TEMPERATURA DEL BLANCO", size=10, weight="bold", color="#a0a0b0"),
                ft.Container(height=15),
                temp_slider,
                ft.Row([
                    ft.Text("Cálido", size=10, color="#a0a0b0"),
                    ft.Text("Frío", size=10, color="#a0a0b0"),
                ], alignment="spaceBetween")
            ]
        ),
        bgcolor="#1a1a24", padding=20, border_radius=15, visible=False
    )

    # --- BRILLO ---
    br_text = ft.Text("70%", size=12, weight="bold", color="#7c3aed")
    brightness_slider = ft.Slider(
        min=1, max=100, divisions=100, value=70, 
        active_color="#7c3aed", inactive_color="#333344",
        on_change_end=on_brightness_change
    )

    br_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Text("Brillo Lámpara", size=12, weight="bold", color="#ffffff"),
                    br_text
                ], alignment="spaceBetween"),
                brightness_slider
            ]
        ),
        bgcolor="#1a1a24", padding=20, border_radius=15
    )

    page.add(
        ft.Column(
            controls=[header, tabs_row, color_panel, white_panel, br_panel],
            spacing=15, width=400 
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
