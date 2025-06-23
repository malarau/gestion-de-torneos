from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class TeamForm(FlaskForm):
    name = StringField(
        'Nombre del Equipo',
        validators=[
            DataRequired(message="El nombre es obligatorio"),
            Length(min=3, max=100, message="El nombre debe tener entre 3 y 100 caracteres")
        ],
        render_kw={"placeholder": "Nombre del equipo"}
    )
    submit = SubmitField('Guardar')