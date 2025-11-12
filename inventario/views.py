from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Inventario, CategoriaProducto, Producto


@login_required
def list_inventory(request):
    query = request.GET.get('buscarProducto')
    producto = Producto.objects.select_related(
        'categoria').prefetch_related('inventarios').all()
    categoria = CategoriaProducto.objects.all()

    # Filtro categoria
    categoria_id = request.GET.get('buscarCategoria')
    if categoria_id and categoria_id.strip():
        try:
            categoria_id_int = int(categoria_id)
            producto = producto.filter(categoria=categoria_id_int)
        except ValueError:
            categoria_id = None

    # Filtrar producto
    if query:
        producto = producto.filter(nombre__icontains=query)

    # datos para las variables html
    context = {
        "productos": producto,
        "categorias": categoria,
        "categoria_seleccionada": categoria_id,
    }

    return render(request, 'inventario/list_inventory.html', context)


@login_required
def create_product(request):
    categorias = CategoriaProducto.objects.all()

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_producto = request.POST.get('nombreProducto')
            categoria_id = request.POST.get('categoria')
            stock_minimo = request.POST.get('stockMinimo')
            precio_compra = request.POST.get('precioCompra')
            precio_venta = request.POST.get('precioVenta')
            unidad_medida = request.POST.get('unidadMedida')
            descripcion = request.POST.get('descripcion')

            # Validaciones básicas
            if not all([nombre_producto, categoria_id, precio_compra, precio_venta]):
                messages.error(
                    request, 'Todos los campos obligatorios deben ser completados.')
                return render(request, 'inventario/create_product.html', {'categorias': categorias})

            # Obtener la categoría
            try:
                categoria = CategoriaProducto.objects.get(id=categoria_id)
            except CategoriaProducto.DoesNotExist:
                messages.error(
                    request, 'La categoría seleccionada no es válida.')
                return render(request, 'inventario/create_product.html', {'categorias': categorias})

            # Generar el código automáticamente
            prefijo = categoria.nombre_categoria[:2].upper()
            # Buscar el último producto de esa categoría
            ultimo_producto = Producto.objects.filter(
                categoria=categoria,
                codigo_producto__startswith=prefijo
            ).order_by('-codigo_producto').first()

            if ultimo_producto:
                # Extraer el número y sumarle 1
                ultimo_numero = int(ultimo_producto.codigo_producto[2:])
                nuevo_numero = ultimo_numero + 1
            else:
                nuevo_numero = 1

            codigo_producto = f"{prefijo}{nuevo_numero:04d}"

            # Verificar que el código no exista (por si acaso)
            if Producto.objects.filter(codigo_producto=codigo_producto).exists():
                messages.error(
                    request, f'Ya existe un producto con el código "{codigo_producto}".')
                return render(request, 'inventario/create_product.html', {'categorias': categorias})

            # Crear el producto
            nuevo_producto = Producto.objects.create(
                codigo_producto=codigo_producto,
                nombre=nombre_producto,
                descripcion=descripcion or '',
                categoria=categoria,
                precio_compra=float(precio_compra),
                precio_venta=float(precio_venta),
                stock_minimo=int(stock_minimo) if stock_minimo else 0,
                unidad_medida=unidad_medida or ''
            )

            messages.success(
                request, f'Producto "{nuevo_producto.nombre}" creado exitosamente con código {codigo_producto}.')
            return redirect('lista_inventario')

        except ValueError:
            messages.error(
                request, 'Error en los valores numéricos. Verifique los precios y stock.')
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')

    context = {
        'categorias': categorias
    }
    return render(request, 'inventario/create_product.html', context)


@login_required
def detail_product(request, producto_id):
    # Obtener el producto o devolver 404 si no existe
    producto = get_object_or_404(Producto, id=producto_id)

    # Obtener el inventario asociado (crear uno si no existe)
    inventario, created = Inventario.objects.get_or_create(
        producto=producto,
        defaults={
            'cantidad_actual': 0,
            'cantidad_reservada': 0,
            'ubicacion_almacen': 'No especificada'
        }
    )

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Actualizar datos del producto
                producto.nombre = request.POST.get('nombre', '').strip()
                producto.descripcion = request.POST.get(
                    'descripcion', '').strip()
                producto.codigo_producto = request.POST.get(
                    'codigo_producto', '').strip()

                # Validar y obtener la categoría
                categoria_id = request.POST.get('categoria')
                if categoria_id:
                    categoria = get_object_or_404(
                        CategoriaProducto, id=categoria_id)
                    producto.categoria = categoria

                # Actualizar precios
                try:
                    producto.precio_compra = float(
                        request.POST.get('precio_compra', 0))
                    producto.precio_venta = float(
                        request.POST.get('precio_venta', 0))
                except (ValueError, TypeError):
                    messages.error(
                        request, 'Los precios deben ser números válidos.')
                    return redirect('detalle_producto', producto_id=producto_id)

                # Actualizar stock mínimo
                try:
                    producto.stock_minimo = int(
                        request.POST.get('stock_minimo', 0))
                except (ValueError, TypeError):
                    messages.error(
                        request, 'El stock mínimo debe ser un número entero válido.')
                    return redirect('detalle_producto', producto_id=producto_id)

                producto.unidad_medida = request.POST.get(
                    'unidad_medida', '').strip()

                # Actualizar datos del inventario
                try:
                    inventario.cantidad_actual = int(
                        request.POST.get('cantidad_actual', 0))
                    inventario.cantidad_reservada = int(
                        request.POST.get('cantidad_reservada', 0))
                except (ValueError, TypeError):
                    messages.error(
                        request, 'Las cantidades deben ser números enteros válidos.')
                    return redirect('detalle_producto', producto_id=producto_id)

                inventario.ubicacion_almacen = request.POST.get(
                    'ubicacion_almacen', 'No especificada').strip()

                # Validaciones adicionales
                if not producto.nombre:
                    messages.error(
                        request, 'El nombre del producto es obligatorio.')
                    return redirect('detalle_producto', producto_id=producto_id)

                if not producto.codigo_producto:
                    messages.error(
                        request, 'El código del producto es obligatorio.')
                    return redirect('detalle_producto', producto_id=producto_id)

                if producto.precio_compra < 0 or producto.precio_venta < 0:
                    messages.error(
                        request, 'Los precios no pueden ser negativos.')
                    return redirect('detalle_producto', producto_id=producto_id)

                if inventario.cantidad_actual < 0 or inventario.cantidad_reservada < 0:
                    messages.error(
                        request, 'Las cantidades no pueden ser negativas.')
                    return redirect('detalle_producto', producto_id=producto_id)

                if inventario.cantidad_reservada > inventario.cantidad_actual:
                    messages.error(
                        request, 'La cantidad reservada no puede ser mayor que la cantidad actual.')
                    return redirect('detalle_producto', producto_id=producto_id)

                # Guardar los cambios
                producto.save()
                inventario.save()

                messages.success(
                    request, 'Producto actualizado correctamente.')
                return redirect('detalle_producto', producto_id=producto_id)

        except Exception as e:
            messages.error(
                request, f'Error al actualizar el producto: {str(e)}')
            return redirect('detalle_producto', producto_id=producto_id)

    # GET request - mostrar el formulario
    # Obtener todas las categorías para el select
    categorias = CategoriaProducto.objects.all().order_by('nombre_categoria')

    for categoria in categorias:
        categoria.is_selected = (categoria.id == producto.categoria.id)

    # Calcular cantidad disponible
    cantidad_disponible = inventario.cantidad_actual - inventario.cantidad_reservada

    # Verificar si está por debajo del stock mínimo
    stock_bajo = inventario.cantidad_actual <= producto.stock_minimo

    context = {
        'producto': producto,
        'inventario': inventario,
        'categorias': categorias,
        'cantidad_disponible': cantidad_disponible,
        'stock_bajo': stock_bajo,
        'created': created,  # Para mostrar si se creó un nuevo inventario
    }

    return render(request, 'inventario/detail_product.html', context)


@login_required
def create_category(request):
    categorias = CategoriaProducto.objects.all()

    if request.method == 'POST':
        nombre_categoria = request.POST.get('nombreCategoria', '').strip()
        descripcion_categoria = request.POST.get(
            'descripcionCategoria', '').strip()

        if not nombre_categoria:
            messages.error(
                request, 'El nombre de la categoría es obligatorio.')
            return render(request, 'inventario/create_product.html', {'categorias': categorias})

        # Verificar si la categoría ya existe
        if CategoriaProducto.objects.filter(nombre_categoria=nombre_categoria).exists():
            messages.error(request, 'Ya existe una categoría con ese nombre.')
            return render(request, 'inventario/create_product.html', {'categorias': categorias})

        # Crear la nueva categoría
        CategoriaProducto.objects.create(
            nombre_categoria=nombre_categoria,
            descripcion=descripcion_categoria
        )

        messages.success(
            request, f'Categoría "{nombre_categoria}" creada exitosamente.')
        return redirect('crear_producto')

    return render(request, 'inventario/create_product.html')
