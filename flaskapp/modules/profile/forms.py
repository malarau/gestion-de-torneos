from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class ProfileForm(FlaskForm):
    name = StringField('Nombre', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    email = StringField('Correo electrónico', render_kw={"disabled": True})
    submit = SubmitField('Actualizar perfil')