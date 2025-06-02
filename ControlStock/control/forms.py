from django import forms  # Importa el módulo de formularios de Django.
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory

from .models import MovimientoStock, Producto, Ubicacion, \
    ProductoAtributo, Atributo, OpcionAtributo, \
    UsuarioPersonalizado  # Importa los modelos relacionados con los formularios.
from django.forms import BaseInlineFormSet, ValidationError

class MovimientoStockForm(forms.ModelForm):
        """
        Formulario para registrar movimientos de stock.
        Hereda de forms.ModelForm y está asociado al modelo MovimientoStock.
        """
        class Meta:
            model = MovimientoStock  # Especifica el modelo al que este formulario está asociado.
            fields = ['producto', 'tipo', 'cantidad', 'ubicacion_origen', 'ubicacion_destino', 'observaciones']  # Define los campos del modelo que se incluirán en el formulario.
            widgets = {
                'observaciones': forms.Textarea(attrs={'rows': 3}),  # Utiliza un widget Textarea para el campo de observaciones con 3 filas.
            }

        def __init__(self, *args, **kwargs):
            """
            Método de inicialización del formulario.
            Se utiliza para personalizar los campos del formulario.
            """
            super().__init__(*args, **kwargs)  # Llama al método __init__ de la clase padre.

            # Filtramos productos activos para el campo 'producto'
            self.fields['producto'].queryset = Producto.objects.filter(activo=True)

            # Filtramos todas las ubicaciones para los campos de origen y destino
            self.fields['ubicacion_origen'].queryset = Ubicacion.objects.all()
            self.fields['ubicacion_destino'].queryset = Ubicacion.objects.all()

            # Los campos de ubicación no son requeridos por defecto, se validan condicionalmente en el método clean.
            self.fields['ubicacion_origen'].required = False
            self.fields['ubicacion_destino'].required = False

            # Añadir la clase CSS 'form-control' a todos los campos del formulario para estilos de Bootstrap.
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

        def clean(self):
            """
            Método para realizar validaciones personalizadas en los datos del formulario.
            Se llama después de la validación de los campos individuales.
            """
            cleaned_data = super().clean()  # Obtiene los datos limpios del formulario.
            tipo = cleaned_data.get('tipo')  # Obtiene el valor del campo 'tipo'.
            cantidad = cleaned_data.get('cantidad')  # Obtiene el valor del campo 'cantidad'.
            producto = cleaned_data.get('producto')  # Obtiene el objeto Producto seleccionado.
            ubicacion_origen = cleaned_data.get('ubicacion_origen')  # Obtiene la ubicación de origen.
            ubicacion_destino = cleaned_data.get('ubicacion_destino')  # Obtiene la ubicación de destino.

            # Validación específica para el tipo de movimiento 'SALIDA'
            if tipo == 'SALIDA':
                if producto and cantidad is not None and producto.stock_actual < cantidad:
                    # Si la cantidad a dar de salida es mayor que el stock actual, levanta un error de validación.
                    raise forms.ValidationError(
                        f"No hay suficiente stock. Stock actual: {producto.stock_actual}"
                    )
                if not ubicacion_origen:
                    # Si el tipo es 'SALIDA' y no se ha seleccionado una ubicación de origen, levanta un error.
                    raise forms.ValidationError("Debe seleccionar una ubicación de origen para las salidas")

            # Validación específica para el tipo de movimiento 'TRASPASO'
            if tipo == 'TRASPASO':
                if not ubicacion_origen or not ubicacion_destino:
                    # Si el tipo es 'TRASPASO' y falta alguna de las ubicaciones, levanta un error.
                    raise forms.ValidationError("Debe seleccionar ambas ubicaciones para traspasos")
                if ubicacion_origen == ubicacion_destino:
                    # Si las ubicaciones de origen y destino son la misma, levanta un error.
                    raise forms.ValidationError("Las ubicaciones de origen y destino deben ser diferentes")

            return cleaned_data  # Devuelve los datos limpios, incluyendo las validaciones personalizadas.

class ProductoAtributoBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

# forms.py
class ProductoAtributoForm(forms.ModelForm):
    class Meta:
        model = ProductoAtributo
        fields = ['atributo', 'opcion']
        widgets = {
            'atributo': forms.Select(attrs={'class': 'form-select atributo-select'}),
            'opcion': forms.Select(attrs={'class': 'form-select opcion-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Si el formulario está marcado para borrar, omitir validación
        if self.cleaned_data.get('DELETE'):
            return cleaned_data

        atributo = cleaned_data.get('atributo')
        opcion = cleaned_data.get('opcion')

        if atributo and not opcion:
            self.add_error('opcion', 'Debe seleccionar una opción para el atributo.')
        elif opcion and opcion.atributo != atributo:
            self.add_error('opcion', 'La opción seleccionada no pertenece al atributo.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opcion'].queryset = OpcionAtributo.objects.none()
        self.fields['opcion'].required = True  # Asegurar que el campo sea requerido

        if 'atributo' in self.data:
            try:
                atributo_id = int(self.data.get('atributo'))
                self.fields['opcion'].queryset = OpcionAtributo.objects.filter(atributo_id=atributo_id)
                self.fields['opcion'].required = True
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.atributo:
            self.fields['opcion'].queryset = self.instance.atributo.opciones.all()
            self.fields['opcion'].required = True

    def clean(self):
        cleaned_data = super().clean()
        atributo = cleaned_data.get('atributo')
        opcion = cleaned_data.get('opcion')

        if atributo and not opcion:
            self.add_error('opcion', 'Debe seleccionar una opción para el atributo.')
        elif opcion and opcion.atributo != atributo:
            self.add_error('opcion', 'La opción seleccionada no pertenece al atributo.')
ProductoAtributoFormSet = forms.inlineformset_factory(
    Producto,
    ProductoAtributo,
    form=ProductoAtributoForm,
    extra=1,
    can_delete=True
)
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo_barras', 'nombre', 'categoria', 'precio_compra',
            'precio_venta', 'stock_actual', 'stock_minimo', 'descripcion',
            'imagen'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo_barras'].required = False  # No obligatorio
class ReporteErrorForm(forms.Form):
    """
    Formulario para que los usuarios reporten errores o problemas.
    No está directamente asociado a un modelo de base de datos.
    """
    asunto = forms.CharField(label="Asunto", max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Título breve del error',
    }))  # Campo para el asunto del reporte, con un widget TextInput y atributos HTML.
    descripcion = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Describe el error lo más detalladamente posible...',
        'rows': 5
    }))  # Campo para la descripción del error, con un widget Textarea y atributos HTML.
    email = forms.EmailField(label="Correo electrónico", required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'tu@correo.com'
    }))  # Campo opcional para el correo electrónico del reportante, con un widget EmailInput y atributos HTML.


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    departamento = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(choices=UsuarioPersonalizado.ROLES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = UsuarioPersonalizado
        fields = (
            'username',
            'email',
            'telefono',
            'departamento',
            'rol',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadimos clases de Bootstrap a cada campo
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Usuario'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Repetir contraseña'})
