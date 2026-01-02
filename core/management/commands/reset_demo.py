from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from faker import Faker
from decimal import Decimal
import random
from datetime import timedelta

# Importa tus modelos
from clientes.models import Cliente
from inventario.models import CategoriaProducto, Producto, Inventario
from pedidos.models import OrdenVenta, DetalleOrdenVenta, PedidoProveedor, DetallePedidoProveedor
from proveedores.models import Proveedor

fake = Faker('es_ES')


class Command(BaseCommand):
    help = 'Resetea la base de datos con datos dummy para demo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-flush',
            action='store_true',
            help='No borra la BD, solo añade datos'
        )
        parser.add_argument(
            '--productos',
            type=int,
            default=50,
            help='Cantidad de productos a crear (default: 50)'
        )
        parser.add_argument(
            '--clientes',
            type=int,
            default=20,
            help='Cantidad de clientes a crear (default: 20)'
        )
        parser.add_argument(
            '--ordenes',
            type=int,
            default=30,
            help='Cantidad de órdenes de venta a crear (default: 30)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '🔄 Iniciando reset de base de datos MyStock...'))

        try:
            with transaction.atomic():
                if not options['skip_flush']:
                    self.stdout.write('🗑️  Limpiando base de datos...')
                    # Limpia solo las tablas de tu app, no las de Django/Axes
                    self._clean_database()

                self.stdout.write('👤 Creando usuarios...')
                admin_user, demo_user = self._create_users()

                self.stdout.write('📦 Creando categorías de productos...')
                categorias = self._create_categorias()

                self.stdout.write('🏭 Creando proveedores...')
                proveedores = self._create_proveedores()

                self.stdout.write('📦 Creando productos...')
                productos = self._create_productos(
                    categorias, options['productos'])

                self.stdout.write('📊 Creando inventario...')
                self._create_inventario(productos)

                self.stdout.write('👥 Creando clientes...')
                clientes = self._create_clientes(
                    admin_user, demo_user, options['clientes'])

                self.stdout.write('🛒 Creando órdenes de venta...')
                self._create_ordenes_venta(
                    clientes, productos, admin_user, demo_user, options['ordenes'])

                self.stdout.write('📥 Creando pedidos a proveedores...')
                self._create_pedidos_proveedor(
                    proveedores, productos, admin_user, demo_user)

                self.stdout.write(self.style.SUCCESS(
                    '\n✅ Reset completado exitosamente'))
                self._print_summary(options)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise

    def _clean_database(self):
        """Limpia solo las tablas de negocio, preserva Django admin"""
        DetalleOrdenVenta.objects.all().delete()
        DetallePedidoProveedor.objects.all().delete()
        OrdenVenta.objects.all().delete()
        PedidoProveedor.objects.all().delete()
        Inventario.objects.all().delete()
        Producto.objects.all().delete()
        CategoriaProducto.objects.all().delete()
        Cliente.objects.all().delete()
        Proveedor.objects.all().delete()
        # Mantén usuarios admin si existen, borra solo demo
        User.objects.filter(username__in=['demo', 'admin']).delete()

    def _create_users(self):
        """Crea usuarios de prueba"""

        demo = User.objects.create_user(
            username='demo',
            email='demo@mystock.com',
            password='demo123',
            first_name='Usuario',
            last_name='Demo',
            is_staff=False,  # Sin acceso al admin
            is_active=True
        )
        self.stdout.write('  ✓ Demo: demo/demo123 (sin permisos admin)')

        return admin, demo

    def _create_categorias(self):
        """Crea categorías de productos"""
        categorias_nombres = [
            ('Electrónica', 'Productos electrónicos y componentes'),
            ('Herramientas', 'Herramientas manuales y eléctricas'),
            ('Materiales de Construcción', 'Cemento, arena, ladrillos, etc.'),
            ('Fontanería', 'Tuberías, grifos y accesorios'),
            ('Electricidad', 'Cables, enchufes y componentes eléctricos'),
            ('Pintura', 'Pinturas, brochas y accesorios'),
            ('Ferretería', 'Tornillos, clavos, bisagras, etc.'),
            ('Jardinería', 'Herramientas y productos para jardín'),
        ]

        categorias = []
        for nombre, desc in categorias_nombres:
            cat = CategoriaProducto.objects.create(
                nombre_categoria=nombre,
                descripcion=desc,
                creado_el=timezone.now(),
                actualizado_el=timezone.now()
            )
            categorias.append(cat)

        self.stdout.write(f'  ✓ {len(categorias)} categorías creadas')
        return categorias

    def _create_proveedores(self):
        """Crea proveedores"""
        proveedores = []
        for i in range(10):
            proveedor = Proveedor.objects.create(
                nombre_empresa=fake.company(),
                contacto_nombre=fake.name(),
                email=fake.company_email(),
                telefono_oficina=fake.phone_number()[:17],
                telefono_segundario=fake.phone_number()[:17] if random.choice(
                    [True, False]
                ) else None,
                direccion=fake.address(),
                ciudad=fake.city(),
                codigo_postal=random.randint(35000, 38999),
                cif=f'{random.choice(["A", "B"])}{random.randint(10000000, 99999999)}',
                condiciones_pago=random.choice(
                    ['30 días', '60 días', '90 días', 'Contado']),
                creado_el=timezone.now(),
                actualizado_el=timezone.now()
            )
            proveedores.append(proveedor)

        self.stdout.write(f'  ✓ {len(proveedores)} proveedores creados')
        return proveedores

    def _create_productos(self, categorias, cantidad):
        """Crea productos con códigos únicos"""
        productos = []
        prefijos = ['PROD', 'ART', 'REF', 'SKU']

        for i in range(cantidad):
            codigo = f'{random.choice(prefijos)}-{i+1:05d}'
            precio_compra = Decimal(str(round(random.uniform(5, 500), 2)))
            margen = Decimal(str(round(random.uniform(1.2, 2.5), 2)))

            producto = Producto.objects.create(
                codigo_producto=codigo,
                nombre=fake.catch_phrase()[:200],
                descripcion=fake.text(max_nb_chars=300),
                precio_compra=precio_compra,
                precio_venta=precio_compra * margen,
                stock_minimo=random.randint(5, 50),
                unidad_medida=random.choice(
                    ['Unidad', 'Caja', 'Metro', 'Litro', 'Kilo']),
                categoria=random.choice(categorias),
                creado_el=timezone.now(),
                actualizado_el=timezone.now()
            )
            productos.append(producto)

        self.stdout.write(f'  ✓ {cantidad} productos creados')
        return productos

    def _create_inventario(self, productos):
        """Crea registros de inventario"""
        ubicaciones = [
            'A-01', 'A-02', 'B-01', 'B-02', 'C-01', 'PATIO', 'DEPOSITO']

        for producto in productos:
            Inventario.objects.create(
                producto=producto,
                cantidad_actual=random.randint(0, 200),
                cantidad_reservada=random.randint(0, 10),
                ubicacion_almacen=random.choice(ubicaciones),
                fecha_ultimo_movimiento=timezone.now() - timedelta(days=random.randint(0, 30)),
                creado_el=timezone.now(),
                actualizado_el=timezone.now()
            )

        self.stdout.write(
            f'  ✓ {len(productos)} registros de inventario creados')

    def _create_clientes(self, admin_user, demo_user, cantidad):
        """Crea clientes"""
        clientes = []
        empleados = [admin_user, demo_user]

        for i in range(cantidad):
            cliente = Cliente.objects.create(
                nombre_comercial=fake.company(),
                email=fake.company_email(),
                telefono_oficina=fake.phone_number()[:17],
                telefono_adicional=fake.phone_number()[:17] if random.choice([
                    True, False]) else None,
                direccion_fiscal=fake.address(),
                direccion_entrega=fake.address() if random.choice(
                    [True, False]) else None,
                ciudad_entrega=fake.city() if random.choice(
                    [True, False]) else None,
                codigo_postal_entrega=random.randint(
                    35000, 38999) if random.choice([True, False]) else None,
                ciudad_fiscal=fake.city(),
                codigo_postal_fiscal=random.randint(35000, 38999),
                cif=f'{random.choice(["A", "B", "C"])}{random.randint(10000000, 99999999)}',
                activo=random.choice([True, True, True, False]),  # 75% activos
                empleado_asignado=random.choice(
                    empleados) if random.choice([True, False]) else None,
                creado_el=timezone.now(),
                actualizado_el=timezone.now()
            )
            clientes.append(cliente)

        self.stdout.write(f'  ✓ {cantidad} clientes creados')
        return clientes

    def _create_ordenes_venta(self, clientes, productos, admin_user, demo_user, cantidad):
        """Crea órdenes de venta con detalles"""
        estados = [
            'pendiente', 'procesando', 'entregado', 'cancelado']
        metodos_pago = ['Transferencia', 'Contado',
                        'Tarjeta', 'Cheque', '30 días', '60 días']
        empleados = [admin_user, demo_user]

        for i in range(cantidad):
            fecha_orden = fake.date_between(
                start_date='-90d', end_date='today')
            fecha_entrega = fecha_orden + timedelta(days=random.randint(1, 30))

            orden = OrdenVenta.objects.create(
                numero_orden=f'OV-{timezone.now().year}-{i+1:05d}',
                cliente=random.choice(clientes),
                fecha_orden=fecha_orden,
                fecha_entrega=fecha_entrega,
                estado=random.choice(estados),
                subtotal=Decimal('0.00'),
                descuento=Decimal('0.00'),
                impuestos=Decimal('0.00'),
                total=Decimal('0.00'),
                metodo_pago=random.choice(metodos_pago),
                notas=fake.text(max_nb_chars=200) if random.choice(
                    [True, False]) else None,
                empleado_creador=random.choice(empleados),
                creado_el=timezone.now(),
                actualizado_el=timezone.now()
            )

            # Crear detalles de la orden
            num_items = random.randint(1, 8)
            subtotal_orden = Decimal('0.00')
            impuestos_orden = Decimal('0.00')

            for _ in range(num_items):
                producto = random.choice(productos)
                cantidad = random.randint(1, 20)
                precio_unitario = producto.precio_venta
                descuento_linea = Decimal(str(round(random.uniform(0, 10), 2)))
                igic_porcentaje = Decimal('7.00')  # IGIC Canarias

                subtotal_linea = (precio_unitario * cantidad) - descuento_linea
                igic_importe = subtotal_linea * \
                    (igic_porcentaje / Decimal('100'))

                DetalleOrdenVenta.objects.create(
                    orden=orden,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    descuento_linea=descuento_linea,
                    igic_porcentaje=igic_porcentaje,
                    igic_importe=igic_importe,
                    subtotal=subtotal_linea,
                    empleado_creador=random.choice(empleados),
                    creado_el=timezone.now(),
                    actualizado_el=timezone.now()
                )

                subtotal_orden += subtotal_linea
                impuestos_orden += igic_importe

            # Actualizar totales de la orden
            descuento_orden = subtotal_orden * \
                Decimal(str(random.uniform(0, 0.05)))
            orden.subtotal = subtotal_orden
            orden.descuento = descuento_orden
            orden.impuestos = impuestos_orden
            orden.total = subtotal_orden - descuento_orden + impuestos_orden
            orden.save()

        self.stdout.write(f'  ✓ {cantidad} órdenes de venta creadas')

    def _create_pedidos_proveedor(self, proveedores, productos, admin_user, demo_user):
        """Crea pedidos a proveedores"""
        estados = [
            'pendiente', 'recibido_completo', 'recibido_parcial', 'cancelado']
        empleados = [admin_user, demo_user]

        for i in range(15):
            fecha_pedido = fake.date_between(
                start_date='-60d', end_date='today')
            fecha_entrega = fecha_pedido + \
                timedelta(days=random.randint(7, 45))

            pedido = PedidoProveedor.objects.create(
                numero_pedido=f'PP-{timezone.now().year}-{i+1:05d}',
                proveedor=random.choice(proveedores),
                fecha_pedido=fecha_pedido,
                fecha_entrega_estimada=fecha_entrega,
                estado=random.choice(estados),
                subtotal=Decimal('0.00'),
                impuestos=Decimal('0.00'),
                total=Decimal('0.00'),
                notas=fake.text(max_nb_chars=200) if random.choice(
                    [True, False]) else None,
                empleado_creador=random.choice(empleados),
                creado_el=timezone.now(),
                actualizado_el=timezone.now()
            )

            # Crear detalles del pedido
            num_items = random.randint(3, 15)
            subtotal_pedido = Decimal('0.00')
            impuestos_pedido = Decimal('0.00')

            for _ in range(num_items):
                producto = random.choice(productos)
                cantidad_pedida = random.randint(10, 100)
                cantidad_recibida = random.randint(0, cantidad_pedida) if pedido.estado in [
                    'RECIBIDO_PARCIAL', 'RECIBIDO'] else 0
                precio_unitario = producto.precio_compra
                igic_porcentaje = Decimal('7.00')

                subtotal_linea = precio_unitario * cantidad_pedida
                igic_importe = subtotal_linea * \
                    (igic_porcentaje / Decimal('100'))

                DetallePedidoProveedor.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad_pedida=cantidad_pedida,
                    cantidad_recibida=cantidad_recibida,
                    precio_unitario=precio_unitario,
                    igic_porcentaje=igic_porcentaje,
                    igic_importe=igic_importe,
                    subtotal=subtotal_linea,
                    empleado_creador=random.choice(empleados),
                    creado_el=timezone.now(),
                    actualizado_el=timezone.now()
                )

                subtotal_pedido += subtotal_linea
                impuestos_pedido += igic_importe

            # Actualizar totales del pedido
            pedido.subtotal = subtotal_pedido
            pedido.impuestos = impuestos_pedido
            pedido.total = subtotal_pedido + impuestos_pedido
            pedido.save()

        self.stdout.write('  ✓ 15 pedidos a proveedores creados')

    def _print_summary(self, options):
        """Imprime resumen de datos creados"""
        self.stdout.write('\n📊 Resumen de datos creados:')
        self.stdout.write(f'   • Usuarios: demo')
        self.stdout.write(
            f'   • Categorías: {CategoriaProducto.objects.count()}')
        self.stdout.write(f'   • Productos: {options["productos"]}')
        self.stdout.write(f'   • Proveedores: {Proveedor.objects.count()}')
        self.stdout.write(f'   • Clientes: {options["clientes"]}')
        self.stdout.write(f'   • Órdenes venta: {options["ordenes"]}')
        self.stdout.write(
            f'   • Pedidos proveedor: {PedidoProveedor.objects.count()}')
        self.stdout.write('\n🔑 Credenciales:')
        self.stdout.write('   • Demo:  demo / demo123\n')
