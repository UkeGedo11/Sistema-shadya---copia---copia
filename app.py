import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# Creado por UkeGedo. Adaptado para Alex Fruver S.A.S.
# Configuración de la base de datos
DB_NAME = 'alexfruver_erp.db' # NOMBRE DE LA BASE DE DATOS ACTUALIZADO

# ==============================================================================
# 1. FUNCIONES DE INICIALIZACIÓN Y TABLAS
# ==============================================================================
def init_db():
    """Inicializa la base de datos y crea las tablas si no existen, asegurando la estructura correcta."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # --- DEFINICIÓN DE TABLAS ---

    # Tabla clientes (Se mantiene igual)
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            contacto TEXT,
            email TEXT,
            telefono TEXT,
            direccion TEXT
        )
    ''')

    # Tabla CATEGORIAS
    c.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Tabla PRODUCTOS (CORREGIDA: Añade 'costo_flete_unitario' y elimina 'DROP TABLE')
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            precio_unitario REAL NOT NULL,
            costo_flete_unitario REAL DEFAULT 0.0,
            stock INTEGER,
            id_categoria INTEGER,         
            unidad_medida TEXT,           
            FOREIGN KEY (id_categoria) REFERENCES categorias(id)
        )
    ''')

    # Tabla pedidos (Simplificada a la versión original sin la columna 'items' JSON)
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER NOT NULL,
            nombre_cliente TEXT NOT NULL,
            fecha_creacion TEXT,
            fecha_entrega_estimada TEXT,
            estado TEXT,
            total REAL,
            FOREIGN KEY (id_cliente) REFERENCES clientes(id)
        )
    ''')

    # Tabla items de pedido
    c.execute('''
        CREATE TABLE IF NOT EXISTS items_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pedido INTEGER NOT NULL,
            id_producto INTEGER NOT NULL,
            nombre_producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (id_pedido) REFERENCES pedidos(id),
            FOREIGN KEY (id_producto) REFERENCES productos(id)
        )
    ''')

    conn.commit()

    # --- INSERCIÓN DE DATOS INICIALES ---

    # 1. POBLACIÓN INICIAL DE CATEGORÍAS (Alex Fruver)
    categorias_iniciales = ["Fruta", "Verdura", "Otros"]
    for cat_nombre in categorias_iniciales:
        try:
            c.execute("INSERT INTO categorias (nombre) VALUES (?)", (cat_nombre,))
        except sqlite3.IntegrityError:
            pass # Si ya existe, no hace nada
    conn.commit()
    
    # 2. Obtener el mapa de IDs de categorías
    c.execute("SELECT id, nombre FROM categorias")
    categorias_map = {nombre: id for id, nombre in c.fetchall()}
    
    id_fruta = categorias_map.get("Fruta")
    id_verdura = categorias_map.get("Verdura")

    # 3. Datos de los 39 Productos (Precio Venta COP/Kg)
    # Formato: (Nombre, id_cat, Precio_Venta_Final)
    productos_data = [
        # --- FRUTAS (15 productos) ---
        ("Mango", id_fruta, 3374), 
        ("Papaya", id_fruta, 1644), 
        ("Piña", id_fruta, 1361),
        ("Banano", id_fruta, 3708), 
        ("Guayaba", id_fruta, 2180), 
        ("Maracuyá", id_fruta, 2081),
        ("Naranja", id_fruta, 2011), 
        ("Limón", id_fruta, 1736), 
        ("Mandarina", id_fruta, 3632),
        ("Manzana", id_fruta, 1614), 
        ("Pera", id_fruta, 3496), 
        ("Durazno", id_fruta, 3705),
        ("Aguacate", id_fruta, 3065), 
        ("Tomate de Di", id_fruta, 1564), 
        ("Mora", id_fruta, 3214),
        
        # --- VERDURAS/HORTALIZAS (24 productos) ---
        ("Lechuga", id_verdura, 2862), 
        ("Repollo", id_verdura, 1384), 
        ("Espinaca", id_verdura, 1377),
        ("Tomate", id_verdura, 1585), 
        ("Pepino", id_verdura, 1995), 
        ("Calabacín", id_verdura, 2041),
        ("Pimentón", id_verdura, 2934), 
        ("Zanahoria", id_verdura, 3251), 
        ("Remolacha", id_verdura, 1366),
        ("Rábano", id_verdura, 3118), 
        ("Cebolla bl", id_verdura, 1931), 
        ("Cebolla rc", id_verdura, 3625),
        ("Ajo", id_verdura, 3408), 
        ("Apio", id_verdura, 3577), 
        ("Cilantro", id_verdura, 3065),
        ("Cebollín", id_verdura, 2654), 
        ("Ají", id_verdura, 2001), 
        ("Jengibre", id_verdura, 2750),
        ("Yuca", id_verdura, 3209), 
        ("Ñame", id_verdura, 2190), 
        ("Brócoli", id_verdura, 3921),
        ("Papa", id_verdura, 1300), 
        ("Plátano", id_verdura, 3766), 
        ("Ahuyama", id_verdura, 3920) 
    ]
    
    # 4. Insertar Productos solo si la tabla está vacía
    c.execute("SELECT COUNT(*) FROM productos")
    if c.fetchone()[0] == 0:
        for nombre, id_cat, precio_venta in productos_data:
            try:
                c.execute("""
                    INSERT INTO productos (nombre, descripcion, precio_unitario, costo_flete_unitario, stock, id_categoria, unidad_medida) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (nombre, 'Producto fresco', precio_venta, 0.0, 100, id_cat, 'Kg')) 
            except sqlite3.IntegrityError:
                pass # Evita error si el nombre ya existía (aunque ya se chequeó si la tabla estaba vacía)
                
    conn.commit()
    conn.close()

# Inicialización de datos
init_db()

if 'current_order_items' not in st.session_state:
    st.session_state.current_order_items = []

# ==============================================================================
# 2. FUNCIONES DE INTERACCIÓN CON LA BASE DE DATOS
# ==============================================================================

# --- Funciones para clientes (Se mantienen igual) ---
def add_cliente_db(nombre, contacto, email, telefono, direccion):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO clientes (nombre, contacto, email, telefono, direccion) VALUES (?, ?, ?, ?, ?)",
              (nombre, contacto, email, telefono, direccion))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_clientes_db():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df.to_dict(orient='records')

def obtener_cliente_por_id_db(id_cliente):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM clientes WHERE id = ?", (id_cliente,))
    cliente_data = c.fetchone()
    conn.close()
    if cliente_data:
        columns = [description[0] for description in c.description]
        return dict(zip(columns, cliente_data))
    return None

def update_cliente_db(id_cliente, nombre, contacto, email, telefono, direccion):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE clientes SET nombre = ?, contacto = ?, email = ?, telefono = ?, direccion = ? WHERE id = ?",
              (nombre, contacto, email, telefono, direccion, id_cliente))
    conn.commit()
    conn.close()

def delete_cliente_db(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()

# --- Funciones para Productos (MODIFICADAS) ---

# Función modificada para incluir id_categoria y unidad_medida
def add_producto_db(nombre, descripcion, precio_unitario, stock, id_categoria, unidad_medida):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. VERIFICACIÓN DE EXISTENCIA
    c.execute("SELECT id FROM productos WHERE nombre = ?", (nombre,))
    if c.fetchone():
        conn.close()
        # Devuelve None para indicar que el producto ya existe
        return None 
    
    # 2. INSERCIÓN (si no existe)
    c.execute("INSERT INTO productos (nombre, descripcion, precio_unitario, stock, id_categoria, unidad_medida) VALUES (?, ?, ?, ?, ?, ?)",
              (nombre, descripcion, precio_unitario, stock, id_categoria, unidad_medida))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

# Función modificada para incluir CATEGORIA y UNIDAD_MEDIDA (con JOIN)
def get_productos_db():
    conn = sqlite3.connect(DB_NAME)
    # Unir productos con categorías para obtener el nombre de la categoría
    query = """
    SELECT 
        p.id, 
        p.nombre, 
        c.nombre AS categoria, 
        p.descripcion, 
        p.precio_unitario, 
        p.stock, 
        p.unidad_medida,
        p.id_categoria -- Mantener el ID para la edición
    FROM productos p
    LEFT JOIN categorias c ON p.id_categoria = c.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')

def obtener_producto_por_id_db(id_producto):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Modificado para traer la categoria y unidad
    c.execute("""
        SELECT p.*, c.nombre AS nombre_categoria 
        FROM productos p 
        LEFT JOIN categorias c ON p.id_categoria = c.id
        WHERE p.id = ?
    """, (id_producto,))
    producto_data = c.fetchone()
    conn.close()
    if producto_data:
        # Nota: La descripción del cursor contendrá las columnas de ambas tablas
        columns = [description[0] for description in c.description] 
        return dict(zip(columns, producto_data))
    return None

# Función modificada para incluir id_categoria y unidad_medida
def update_producto_db(id_producto, nombre, descripcion, precio_unitario, stock, id_categoria, unidad_medida):
    """
    Actualiza la información completa de un producto por su ID.
    
    CORRECCIÓN: Se asegura que el SQL y el tuple de valores tengan 8 elementos, 
    incluyendo costo_flete_unitario con valor 0.0, para asegurar la consistencia con la tabla de productos.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 8 marcadores de posición (?) en el SQL (7 en SET + 1 en WHERE)
    c.execute("""
        UPDATE productos 
        SET 
            nombre = ?, 
            descripcion = ?, 
            precio_unitario = ?, 
            costo_flete_unitario = ?,  
            stock = ?, 
            id_categoria = ?, 
            unidad_medida = ? 
        WHERE id = ?
    """,
    # 8 variables en el tuple, con costo_flete_unitario fijado a 0.0:
    (
        nombre, 
        descripcion, 
        precio_unitario, 
        0.0, # <--- Valor fijo para costo_flete_unitario
        stock, 
        id_categoria, 
        unidad_medida, 
        id_producto
    ))
    conn.commit()
    conn.close()

# Actualizar solo el stock de un producto (Se mantiene igual)
def update_producto_stock_db(id_producto, nueva_cantidad_stock):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE productos SET stock = ? WHERE id = ?",
              (nueva_cantidad_stock, id_producto))
    conn.commit()
    conn.close()

def delete_producto_db(producto_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()

# --- Funciones para Pedidos y Stock (Se mantienen/modificadas ligeramente) ---
def add_pedido_db(id_cliente, nombre_cliente, fecha_creacion, fecha_entrega_estimada, estado, total, items):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Insertar Pedido
    c.execute("INSERT INTO pedidos (id_cliente, nombre_cliente, fecha_creacion, fecha_entrega_estimada, estado, total) VALUES (?, ?, ?, ?, ?, ?)",
              (id_cliente, nombre_cliente, fecha_creacion, fecha_entrega_estimada, estado, total))
    new_pedido_id = c.lastrowid
    # Insertar Ítems del Pedido
    for item in items:
        c.execute("INSERT INTO items_pedido (id_pedido, id_producto, nombre_producto, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                  (new_pedido_id, item['id_producto'], item['nombre_producto'], item['cantidad'], item['precio_unitario'], item['subtotal']))
    
    conn.commit()
    conn.close()
    return new_pedido_id

def get_pedidos_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Obtener pedidos principales
    c.execute("SELECT * FROM pedidos")
    pedidos_data = c.fetchall()
    columns_pedidos = [description[0] for description in c.description]
    pedidos_list = []
    for p_data in pedidos_data:
        pedido_dict = dict(zip(columns_pedidos, p_data))
        # Obtener ítems para cada pedido
        c.execute("SELECT * FROM items_pedido WHERE id_pedido = ?", (pedido_dict['id'],))
        items_data = c.fetchall()
        columns_items = [description[0] for description in c.description]
        pedido_dict['items'] = [dict(zip(columns_items, item)) for item in items_data]
        pedidos_list.append(pedido_dict)
    
    conn.close()
    return pedidos_list

# Función para actualizar estado de pedido y manejar el stock
def update_pedido_estado_db(pedido_id, nuevo_estado):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Primero, obtener el estado actual del pedido para evitar doble descuento
    c.execute("SELECT estado FROM pedidos WHERE id = ?", (pedido_id,))
    estado_anterior = c.fetchone()[0]

    c.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id))

    # Lógica de descuento de stock si pasa a 'Completado'
    if nuevo_estado == "Completado" and estado_anterior != "Completado":
        c.execute("SELECT id_producto, cantidad FROM items_pedido WHERE id_pedido = ?", (pedido_id,))
        items_pedido = c.fetchall()

        for id_producto, cantidad_vendida in items_pedido:
            # Obtener el stock actual
            c.execute("SELECT stock FROM productos WHERE id = ?", (id_producto,))
            stock_actual = c.fetchone()[0]

            nuevo_stock = stock_actual - cantidad_vendida
            
            if nuevo_stock < 0:
                nuevo_stock = 0
                st.warning(f"Advertencia: El stock del producto ID {id_producto} intentó ser negativo. Se estableció en 0.")

            c.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, id_producto))
            st.success(f"Stock actualizado: Producto ID {id_producto} - Cantidad vendida: {cantidad_vendida}. Nuevo stock: {nuevo_stock}")
    
    conn.commit()
    conn.close()


# ==============================================================================
# 3. INTERFAZ DE USUARIO CON STREAMLIT
# ==============================================================================

st.set_page_config(layout="wide", page_title="Alex Fruver ERP - Gestión de Productos Frescos")

# Efecto de hora del día: ¡el tema respira!
hour = datetime.now().hour
glow_intensity = "0.9" if 18 <= hour <= 24 else "0.6"

st.markdown(f"""
<style>
/* Fondo con degradado cósmico + textura de ruido cuántico */
.stApp {{
    background: linear-gradient(135deg, #090415 0%, #1a0b2e 100%) 
                url("https://www.transparenttextures.com/patterns/black-thread.png");
    background-attachment: fixed;
}}

/* Glassmorphism en la barra lateral: translúcido, con borde neón */
[data-testid="stSidebar"] {{
    background: rgba(20, 11, 42, 0.65) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-right: 1px solid rgba(0, 243, 255, {glow_intensity});
    box-shadow: 0 0 20px rgba(106, 0, 255, 0.2);
}}

/* Botones: vidrio neón con micro-interacción */
.stButton > button {{
    background: rgba(0, 243, 255, 0.15);
    color: #E2D9FF;
    border: 1px solid rgba(0, 243, 255, 0.4);
    border-radius: 16px;
    backdrop-filter: blur(8px);
    font-weight: 600;
    transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}}
.stButton > button:hover {{
    background: rgba(0, 243, 255, 0.3);
    box-shadow: 0 0 25px rgba(0, 243, 255, 0.7);
    transform: scale(1.03);
}}

/* Títulos con tipografía grande y transiciones de texto */
h1, h2, h3 {{
    background: linear-gradient(90deg, #00F3FF, #6A00FF);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-weight: 800;
    letter-spacing: -0.5px;
}}
</style>
""", unsafe_allow_html=True)

st.components.v1.html("""
<script>
document.addEventListener('mousemove', (e) => {{
    const x = (e.clientX / window.innerWidth - 0.5) * 20;
    const y = (e.clientY / window.innerHeight - 0.5) * 20;
    document.body.style.backgroundPosition = `calc(50% + ${{x}}px) calc(50% + ${{y}}px)`;
}});
</script>
""", height=0)

st.title("Sistema ERP para Alex Fruver S.A.S.")
st.subheader("Venta y Distribución de Frutas y Verduras Frescas")

# Navegación por módulos
menu = st.sidebar.radio("Módulos del ERP", ["Inicio", "Gestión de Clientes", "Gestión de Productos", "Gestión de Pedidos", "Dashboard/Reportes"])

# Obtener categorías para usarlas en los formularios de producto
conn_temp = sqlite3.connect(DB_NAME)
categorias_data = pd.read_sql_query("SELECT id, nombre FROM categorias", conn_temp).to_dict(orient='records')
conn_temp.close()
categorias_map = {c['nombre']: c['id'] for c in categorias_data}
categoria_options = list(categorias_map.keys())
unidad_options = ["Kg", "Unidad", "Atado", "Mano", "Bolsa", "Libra"]


if menu == "Inicio":
    st.write("Bienvenido al Sistema ERP de Alex Fruver. Selecciona un módulo en el menú de la izquierda.")
    # st.image("https://via.placeholder.com/600x200?text=Alex+Fruver+ERP", caption="Control de Frescura y Calidad", use_container_width=True)
    st.info("Este sistema te permite gestionar clientes, inventario de frutas y verduras, y pedidos.")

elif menu == "Gestión de Clientes":
    st.header("Gestión de Clientes")
    # ... (El código de gestión de clientes se mantiene igual)
    cliente_tab, editar_cliente_tab, eliminar_cliente_tab = st.tabs(["Registrar Nuevo", "Editar Cliente", "Eliminar Cliente"])

    with cliente_tab:
        st.subheader("Registrar Nuevo Cliente")
        with st.form("form_cliente", clear_on_submit=True):
            nombre_cliente = st.text_input("Nombre del Cliente", key="nc")
            contacto_cliente = st.text_input("Persona de Contacto", key="pc")
            email_cliente = st.text_input("Email", key="ec")
            telefono_cliente = st.text_input("Teléfono", key="tc")
            direccion_cliente = st.text_area("Dirección", key="dc")
            submitted_cliente = st.form_submit_button("Guardar Cliente")

            if submitted_cliente:
                if nombre_cliente and contacto_cliente:
                    add_cliente_db(nombre_cliente, contacto_cliente, email_cliente, telefono_cliente, direccion_cliente)
                    st.success(f"Cliente '{nombre_cliente}' registrado con éxito y guardado permanentemente.")
                    st.rerun()
                else:
                    st.error("Por favor, ingresa el nombre y la persona de contacto del cliente.")

    with editar_cliente_tab:
        st.subheader("Editar Cliente Existente")
        clientes_data_edit = get_clientes_db()
        if clientes_data_edit:
            clientes_options_edit = {f"{c['id']} - {c['nombre']}": c['id'] for c in clientes_data_edit}
            selected_cliente_key = st.selectbox(
                "Selecciona el cliente a editar",
                [""] + list(clientes_options_edit.keys()),
                key="edit_cliente_select"
            )

            if selected_cliente_key:
                selected_cliente_id = clientes_options_edit[selected_cliente_key]
                cliente_a_editar = obtener_cliente_por_id_db(selected_cliente_id)

                if cliente_a_editar:
                    with st.form("form_editar_cliente", clear_on_submit=False):
                        st.write(f"Editando Cliente ID: {cliente_a_editar['id']}")
                        edit_nombre = st.text_input("Nombre del Cliente", value=cliente_a_editar['nombre'], key=f"edit_nc_{selected_cliente_id}")
                        edit_contacto = st.text_input("Persona de Contacto", value=cliente_a_editar['contacto'], key=f"edit_pc_{selected_cliente_id}")
                        edit_email = st.text_input("Email", value=cliente_a_editar['email'], key=f"edit_ec_{selected_cliente_id}")
                        edit_telefono = st.text_input("Teléfono", value=cliente_a_editar['telefono'], key=f"edit_tc_{selected_cliente_id}")
                        edit_direccion = st.text_area("Dirección", value=cliente_a_editar['direccion'], key=f"edit_dc_{selected_cliente_id}")
                        submitted_edit_cliente = st.form_submit_button("Actualizar Cliente")

                        if submitted_edit_cliente:
                            if edit_nombre and edit_contacto:
                                update_cliente_db(selected_cliente_id, edit_nombre, edit_contacto, edit_email, edit_telefono, edit_direccion)
                                st.success(f"Cliente '{edit_nombre}' actualizado con éxito.")
                                st.rerun()
                            else:
                                st.error("El nombre y la persona de contacto no pueden estar vacíos.")
                else:
                    st.warning("Cliente no encontrado para edición.")
        else:
            st.info("No hay clientes registrados para editar.")
    
    with eliminar_cliente_tab:
        st.subheader("Eliminar Cliente")
        clientes_data_delete = get_clientes_db()
        if clientes_data_delete:
            clientes_options_delete = {c['nombre']: c['id'] for c in clientes_data_delete}
            cliente_a_eliminar_nombre = st.selectbox("Selecciona el cliente a eliminar", [""] + list(clientes_options_delete.keys()), key="delete_cliente_select")
            if cliente_a_eliminar_nombre:
                cliente_a_eliminar_id = clientes_options_delete[cliente_a_eliminar_nombre]
                if st.button(f"Confirmar Eliminación de {cliente_a_eliminar_nombre}", key="confirm_delete_cliente"):
                    delete_cliente_db(cliente_a_eliminar_id)
                    st.success(f"Cliente '{cliente_a_eliminar_nombre}' eliminado permanentemente.")
                    st.rerun()
        else:
            st.info("No hay clientes registrados para eliminar.")

    st.markdown("---")
    st.subheader("Listado de Clientes")
    clientes_data_display = get_clientes_db()
    if clientes_data_display:
        df_clientes = pd.DataFrame(clientes_data_display)
        st.dataframe(df_clientes, use_container_width=True)
    else:
        st.info("No hay clientes registrados aún.")


elif menu == "Gestión de Productos": # TÍTULO CAMBIADO
    st.header("Gestión de Frutas, Verduras y Hortalizas") # TÍTULO CAMBIADO

    # Tabs para organizar las acciones de producto
    producto_tab, editar_producto_tab, ajustar_stock_tab, eliminar_producto_tab = st.tabs(["Registrar Nuevo", "Editar Producto", "Ajustar Stock", "Eliminar Producto"])

    with producto_tab:
        st.subheader("Registrar Nuevo Producto")
        with st.form("form_producto", clear_on_submit=True):
            nombre_producto = st.text_input("Nombre del Producto (Ej: Mango, Lechuga)", key="np")
            
            col_cat, col_uni = st.columns(2)
            with col_cat:
                categoria_seleccionada = st.selectbox("Categoría", categoria_options, key="cat_sel")
            with col_uni:
                unidad_medida_sel = st.selectbox("Unidad de Venta/Inventario", unidad_options, key="um_sel")
            
            descripcion_producto = st.text_area("Descripción (Ej: Calidad extra, Maduro)", key="dp")
            precio_producto = st.number_input("Precio Unitario ($)", min_value=0.01, format="%.2f", key="pp")
            stock_producto = st.number_input("Stock (Cantidad Inicial)", min_value=0, value=0, step=1, key="sp")
            submitted_producto = st.form_submit_button("Guardar Producto")

            if submitted_producto:
                id_categoria_seleccionada = categorias_map.get(categoria_seleccionada) 
                
                if nombre_producto and precio_producto > 0 and id_categoria_seleccionada:
                    # Llamada a la función actualizada con id_categoria y unidad_medida
                    # AQUÍ ES DONDE CAMBIA LA LÓGICA: Captura el valor de retorno
                    new_id = add_producto_db(nombre_producto, descripcion_producto, precio_producto, stock_producto, id_categoria_seleccionada, unidad_medida_sel)
                    
                    if new_id:
                        st.success(f"Producto '{nombre_producto}' registrado con éxito.")
                        st.rerun()
                    else:
                        # Este mensaje se mostrará si new_id es None (producto duplicado)
                        st.error(f"❌ Error de registro: El producto con nombre '{nombre_producto}' ya está registrado en la base de datos.")
                else:
                    st.error("Por favor, ingresa el nombre, un precio unitario válido y una categoría.")
    
    with editar_producto_tab:
        st.subheader("Editar Producto Existente")
        productos_data_edit = get_productos_db()
        if productos_data_edit:
            productos_options_edit = {f"{p['id']} - {p['nombre']} ({p.get('categoria', 'N/A')})": p['id'] for p in productos_data_edit}
            selected_producto_key = st.selectbox(
                "Selecciona el producto a editar",
                [""] + list(productos_options_edit.keys()),
                key="edit_producto_select"
            )

            if selected_producto_key:
                selected_producto_id = productos_options_edit[selected_producto_key]
                producto_a_editar = obtener_producto_por_id_db(selected_producto_id)

                if producto_a_editar:
                    # Obtener la posición del valor actual para el selectbox
                    current_cat_name = producto_a_editar.get('nombre_categoria', categoria_options[0])
                    current_cat_index = categoria_options.index(current_cat_name) if current_cat_name in categoria_options else 0
                    
                    current_unit_name = producto_a_editar.get('unidad_medida', unidad_options[0])
                    current_unit_index = unidad_options.index(current_unit_name) if current_unit_name in unidad_options else 0

                    with st.form("form_editar_producto", clear_on_submit=False):
                        st.write(f"Editando Producto ID: {producto_a_editar['id']}")
                        edit_nombre_prod = st.text_input("Nombre del Producto", value=producto_a_editar['nombre'], key=f"edit_np_{selected_producto_id}")
                        
                        col_cat_e, col_uni_e = st.columns(2)
                        with col_cat_e:
                            edit_categoria_sel = st.selectbox("Categoría", categoria_options, index=current_cat_index, key=f"edit_cat_sel_{selected_producto_id}")
                        with col_uni_e:
                            edit_unidad_medida_sel = st.selectbox("Unidad de Venta/Inventario", unidad_options, index=current_unit_index, key=f"edit_um_sel_{selected_producto_id}")
                        
                        edit_descripcion_prod = st.text_area("Descripción", value=producto_a_editar['descripcion'], key=f"edit_dp_{selected_producto_id}")
                        edit_precio_prod = st.number_input("Precio Unitario", min_value=0.01, format="%.2f", value=float(producto_a_editar['precio_unitario']), key=f"edit_pp_{selected_producto_id}")
                        edit_stock_prod = st.number_input("Stock", min_value=0, value=producto_a_editar['stock'], step=1, key=f"edit_sp_{selected_producto_id}")
                        
                        submitted_edit_producto = st.form_submit_button("Actualizar Producto")

                        if submitted_edit_producto:
                            edit_id_categoria = categorias_map.get(edit_categoria_sel)

                            if edit_nombre_prod and edit_precio_prod > 0 and edit_id_categoria:
                                # Llamada a la función de actualización modificada
                                update_producto_db(selected_producto_id, edit_nombre_prod, edit_descripcion_prod, edit_precio_prod, edit_stock_prod, edit_id_categoria, edit_unidad_medida_sel)
                                st.success(f"Producto '{edit_nombre_prod}' actualizado con éxito.")
                                st.rerun()
                            else:
                                st.error("El nombre, el precio unitario y la categoría no pueden estar vacíos o ser cero.")
                else:
                    st.warning("Producto no encontrado para edición.")
        else:
            st.info("No hay productos o servicios registrados para editar.")

    with ajustar_stock_tab:
        st.subheader("Ajustar Stock de Producto")
        productos_data_stock = get_productos_db()
        if productos_data_stock:
            productos_options_stock = {f"{p['id']} - {p['nombre']} (Stock actual: {p['stock']} {p.get('unidad_medida', '')})": p['id'] for p in productos_data_stock}
            selected_producto_stock_key = st.selectbox(
                "Selecciona el producto para ajustar stock",
                [""] + list(productos_options_stock.keys()),
                key="ajustar_stock_select"
            )

            if selected_producto_stock_key:
                selected_producto_stock_id = productos_options_stock[selected_producto_stock_key]
                producto_a_ajustar = obtener_producto_por_id_db(selected_producto_stock_id)

                if producto_a_ajustar:
                    st.write(f"Producto: **{producto_a_ajustar['nombre']}** ({producto_a_ajustar.get('unidad_medida', 'N/A')})")
                    st.write(f"Stock actual: **{producto_a_ajustar['stock']}**")
                    
                    ajuste_tipo = st.radio("Tipo de ajuste", ["Añadir Stock", "Restar Stock"], key="ajuste_tipo")
                    cantidad_ajuste = st.number_input("Cantidad a ajustar", min_value=1, value=1, step=1, key="cantidad_ajuste")
                    
                    if st.button("Aplicar Ajuste de Stock", key="confirm_ajuste_stock"):
                        nuevo_stock = producto_a_ajustar['stock']
                        if ajuste_tipo == "Añadir Stock":
                            nuevo_stock += cantidad_ajuste
                            st.success(f"Se añadieron {cantidad_ajuste} unidades al stock.")
                        elif ajuste_tipo == "Restar Stock":
                            if nuevo_stock >= cantidad_ajuste:
                                nuevo_stock -= cantidad_ajuste
                                st.success(f"Se restaron {cantidad_ajuste} unidades del stock.")
                            else:
                                st.warning(f"No hay suficiente stock para restar {cantidad_ajuste} unidades. Stock actual: {nuevo_stock}.")
                                nuevo_stock = 0 
                                
                        update_producto_stock_db(selected_producto_stock_id, nuevo_stock)
                        st.info(f"Nuevo stock para '{producto_a_ajustar['nombre']}': {nuevo_stock}")
                        st.rerun()
                else:
                    st.warning("Producto no encontrado para ajustar stock.")
        else:
            st.info("No hay productos registrados para ajustar stock.")

    with eliminar_producto_tab:
        st.subheader("Eliminar Producto")
        productos_data_delete = get_productos_db()
        if productos_data_delete:
            productos_options_delete = {p['nombre']: p['id'] for p in productos_data_delete}
            producto_a_eliminar_nombre = st.selectbox("Selecciona el producto a eliminar", [""] + list(productos_options_delete.keys()), key="delete_producto_select")
            if producto_a_eliminar_nombre:
                producto_a_eliminar_id = productos_options_delete[producto_a_eliminar_nombre]
                if st.button(f"Confirmar Eliminación de {producto_a_eliminar_nombre}", key="confirm_delete_producto"):
                    delete_producto_db(producto_a_eliminar_id)
                    st.success(f"Producto '{producto_a_eliminar_nombre}' eliminado permanentemente.")
                    st.rerun()
        else:
            st.info("No hay productos registrados para eliminar.")

    st.markdown("---")
    st.subheader("Listado de Productos en Inventario")
    productos_data_display = get_productos_db()
    if productos_data_display:
        df_productos = pd.DataFrame(productos_data_display)
        # Mostrar las columnas actualizadas con nombre de categoría y unidad
        st.dataframe(df_productos[['id', 'nombre', 'categoria', 'unidad_medida', 'precio_unitario', 'stock', 'descripcion']], use_container_width=True)
    else:
        st.info("No hay productos registrados aún.")

elif menu == "Gestión de Pedidos":
    st.header("Gestión de Pedidos y Ventas") # TÍTULO CAMBIADO

    clientes_data = get_clientes_db()
    productos_data = get_productos_db()

    if not clientes_data:
        st.warning("Para crear un pedido, primero debes registrar clientes en la sección 'Gestión de Clientes'.")
    if not productos_data:
        st.warning("Para crear un pedido, primero debes registrar productos/servicios en la sección 'Gestión de Productos'.")

    if clientes_data and productos_data:
        crear_pedido_tab, actualizar_estado_tab = st.tabs(["Crear Nuevo Pedido", "Actualizar Estado de Pedido"])

        with crear_pedido_tab:
            st.subheader("Crear Nuevo Pedido de Fruver")

            with st.form("form_pedido_principal", clear_on_submit=False):
                clientes_map = {c['nombre']: c['id'] for c in clientes_data}
                cliente_seleccionado_nombre = st.selectbox(
                    "Selecciona el Cliente",
                    list(clientes_map.keys()) if clientes_map else [],
                    key="sel_cliente_pedido"
                )
                id_cliente_pedido = clientes_map[cliente_seleccionado_nombre] if cliente_seleccionado_nombre else None

                fecha_entrega = st.date_input("Fecha de Entrega Estimada", datetime.now(), key="fecha_entrega_pedido")
                estado_pedido = st.selectbox("Estado del Pedido", ["Pendiente", "En Proceso", "Completado", "Cancelado"], key="estado_pedido_sel")

                if st.session_state.current_order_items:
                    st.write("---")
                    st.subheader("Ítems del Pedido Actual")
                    df_current_items = pd.DataFrame(st.session_state.current_order_items)
                    st.dataframe(df_current_items[['nombre_producto', 'cantidad', 'precio_unitario', 'subtotal']], use_container_width=True)
                    total_pedido = df_current_items['subtotal'].sum()
                    st.markdown(f"### Total del Pedido: ${total_pedido:,.2f}")
                    st.write("---")
                else:
                    total_pedido = 0

                submitted_pedido = st.form_submit_button("Guardar Pedido")

                if submitted_pedido:
                    if id_cliente_pedido and st.session_state.current_order_items:
                        add_pedido_db(
                            id_cliente_pedido,
                            cliente_seleccionado_nombre,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            fecha_entrega.strftime("%Y-%m-%d"),
                            estado_pedido,
                            total_pedido,
                            st.session_state.current_order_items
                        )
                        st.success(f"Pedido para '{cliente_seleccionado_nombre}' guardado con éxito y de forma permanente.")
                        st.session_state.current_order_items = []
                        st.rerun()
                    else:
                        st.error("Asegúrate de seleccionar un cliente y añadir al menos un ítem al pedido.")

            st.subheader("Añadir Productos al Pedido Actual")
            with st.form("form_add_item", clear_on_submit=True):
                # Usar el ID y nombre del producto junto con la unidad para claridad
                productos_map = {f"{p['nombre']} ({p.get('unidad_medida', 'N/A')})": p['id'] for p in productos_data}
                
                producto_a_agregar_display = st.selectbox("Producto a añadir", [""] + list(productos_map.keys()), key="paa_item")
                cantidad_a_agregar = st.number_input("Cantidad", min_value=1, value=1, step=1, key="caa_item")

                submitted_add_item = st.form_submit_button("Añadir Ítem")

                if submitted_add_item:
                    if producto_a_agregar_display and cantidad_a_agregar > 0:
                        id_producto_pedido_item = productos_map[producto_a_agregar_display]
                        producto_obj = obtener_producto_por_id_db(id_producto_pedido_item)
                        if producto_obj:
                            if producto_obj['stock'] is not None and producto_obj['stock'] < cantidad_a_agregar:
                                st.warning(f"¡Atención! No hay suficiente stock de '{producto_obj['nombre']}'. Disponible: {producto_obj['stock']} {producto_obj.get('unidad_medida', 'N/A')}. Cantidad solicitada: {cantidad_a_agregar}.")
                            else:
                                subtotal = producto_obj['precio_unitario'] * cantidad_a_agregar
                                st.session_state.current_order_items.append({
                                    'id_producto': id_producto_pedido_item,
                                    'nombre_producto': producto_obj['nombre'],
                                    'cantidad': cantidad_a_agregar,
                                    'precio_unitario': producto_obj['precio_unitario'],
                                    'subtotal': subtotal
                                })
                                st.success(f"'{producto_obj['nombre']}' añadido al pedido.")
                        else:
                            st.error("Producto no encontrado.")
                    else:
                        st.warning("Selecciona un producto y una cantidad válida.")

        with actualizar_estado_tab:
            st.subheader("Actualizar Estado de Pedido")
            pedidos_data_update = get_pedidos_db()
            if pedidos_data_update:
                pedido_options = {f"ID: {p['id']} - Cliente: {p['nombre_cliente']} - Estado actual: {p['estado']}": p['id'] for p in pedidos_data_update}
                
                selected_pedido_display = st.selectbox(
                    "Selecciona el pedido a actualizar", 
                    [""] + list(pedido_options.keys()), 
                    key="update_pedido_id_sel"
                )

                if selected_pedido_display:
                    pedido_a_actualizar_id = pedido_options[selected_pedido_display]
                    pedido_obj = next((p for p in pedidos_data_update if p['id'] == pedido_a_actualizar_id), None)
                    if pedido_obj:
                        current_index = ["Pendiente", "En Proceso", "Completado", "Cancelado"].index(pedido_obj['estado'])
                        nuevo_estado = st.selectbox(
                            f"Nuevo estado para Pedido #{pedido_a_actualizar_id} (Cliente: {pedido_obj['nombre_cliente']})", 
                            ["Pendiente", "En Proceso", "Completado", "Cancelado"], 
                            index=current_index,
                            key=f"nuevo_estado_sel_{pedido_a_actualizar_id}"
                        )
                        if st.button("Actualizar Estado del Pedido", key=f"btn_update_estado_{pedido_a_actualizar_id}"):
                            update_pedido_estado_db(pedido_a_actualizar_id, nuevo_estado)
                            st.success(f"Estado del Pedido #{pedido_a_actualizar_id} actualizado a '{nuevo_estado}'.")
                            st.rerun()
                    else:
                        st.error("Pedido no encontrado.")
            else:
                st.info("No hay pedidos registrados para actualizar.")

        st.markdown("---")
        st.subheader("Listado de Pedidos")
        pedidos_data_display = get_pedidos_db()
        if pedidos_data_display:
            pedidos_data_for_df = []
            for p in pedidos_data_display:
                pedidos_data_for_df.append({
                    'ID Pedido': p['id'],
                    'Cliente': p['nombre_cliente'],
                    'Fecha Creación': p['fecha_creacion'],
                    'Fecha Entrega Est.': p['fecha_entrega_estimada'],
                    'Estado': p['estado'],
                    'Total': f"${p['total']:,.2f}",
                    'Ítems': ", ".join([f"{item['nombre_producto']} (x{item['cantidad']})" for item in p['items']])
                })
            df_pedidos = pd.DataFrame(pedidos_data_for_df)
            st.dataframe(df_pedidos, use_container_width=True)
        else:
            st.info("No hay pedidos registrados aún.")

elif menu == "Dashboard/Reportes":
    st.header("Dashboard y Reportes Operacionales")

    clientes_data = get_clientes_db()
    productos_data = get_productos_db() # Esta es la función que hace el JOIN
    pedidos_data = get_pedidos_db()

    st.subheader("Resumen General")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Total Clientes", value=len(clientes_data))
    with col2:
        st.metric(label="Total Productos en Catálogo", value=len(productos_data))
    with col3:
        st.metric(label="Total Pedidos Registrados", value=len(pedidos_data))

    st.markdown("---")

    st.subheader("Análisis de Pedidos")

    if pedidos_data:
        df_pedidos_analisis = pd.DataFrame(pedidos_data)

        st.write("#### Pedidos por Estado")
        estado_counts = df_pedidos_analisis['estado'].value_counts().reset_index()
        estado_counts.columns = ['Estado', 'Número de Pedidos']
        st.bar_chart(estado_counts.set_index('Estado'))

        st.write("#### Ingresos Totales por Pedidos")
        ingresos_totales = df_pedidos_analisis['total'].sum()
        st.metric(label="Ingresos Acumulados", value=f"${ingresos_totales:,.2f}")

        st.write("#### Productos Más Vendidos (por Cantidad)")
        all_items = []
        for pedido in pedidos_data:
            for item in pedido['items']:
                all_items.append(item)

        if all_items:
            df_all_items = pd.DataFrame(all_items)
            
            # 1. Agrupar por nombre_producto y sumar la cantidad vendida
            top_productos = df_all_items.groupby('nombre_producto')['cantidad'].sum().reset_index()
            top_productos.columns = ['Producto', 'Cantidad Vendida']
            
            # 2. Convertir productos_data a DataFrame y mapear la Unidad de Medida
            df_productos_catalogo = pd.DataFrame(productos_data)[['nombre', 'unidad_medida']]
            # Nombra la columna 'Unidad' para el merge
            df_productos_catalogo.columns = ['Producto', 'Unidad'] 
            
            # 3. Combinar (Merge) el reporte de ventas con la unidad de medida del catálogo
            top_productos = pd.merge(top_productos, df_productos_catalogo, on='Producto', how='left')
            
            # 4. (ELIMINADO el paso de concatenar el número)
            #    Simplemente renombramos 'Unidad' a 'Unidad de Venta' para la visualización final
            top_productos.rename(columns={'Unidad': 'Unidad de Venta'}, inplace=True) 
            
            top_productos = top_productos.sort_values(by='Cantidad Vendida', ascending=False)

            # Mostrar la tabla con la columna 'Unidad de Venta' (solo el texto: Kg, Unidad, etc.)
            st.dataframe(top_productos[['Producto', 'Unidad de Venta', 'Cantidad Vendida']], use_container_width=True)
            
            # Gráfico sigue usando solo la Cantidad Vendida
            st.bar_chart(top_productos.set_index('Producto')['Cantidad Vendida'])

        st.markdown("---")
        st.write("#### Reporte de Stock de Productos")
        if productos_data:
            df_productos_stock = pd.DataFrame(productos_data)
            
            # MODIFICADO: Muestra las columnas relevantes para Alex Fruver
            df_productos_stock_display = df_productos_stock[['nombre', 'categoria', 'unidad_medida', 'stock', 'precio_unitario']]
            df_productos_stock_display.columns = ['Producto', 'Categoría', 'Unidad', 'Stock Actual', 'Precio Unitario']
            st.dataframe(df_productos_stock_display, use_container_width=True)

            # Opcional: Alertas de stock mínimo
            st.write("##### Alertas de Stock Bajo")
            low_stock_threshold = st.slider("Umbral de alerta de stock mínimo", 0, 50, 10, key="stock_slider")
            
            productos_bajo_stock = df_productos_stock[df_productos_stock['stock'] <= low_stock_threshold]
            if not productos_bajo_stock.empty:
                st.warning(f"¡Alerta! Los siguientes productos tienen stock igual o menor a **{low_stock_threshold}**:")
                # Muestra las columnas relevantes para la alerta
                st.dataframe(productos_bajo_stock[['nombre', 'categoria', 'stock', 'unidad_medida']], use_container_width=True)
            else:
                st.info(f"Ningún producto por debajo del umbral de stock de {low_stock_threshold}.")


        else:
            st.info("No hay productos registrados para mostrar el stock.")
    else:
        st.info("No hay pedidos registrados para generar reportes.")