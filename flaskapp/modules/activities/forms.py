from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, NumberRange

class ActivityForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    description = TextAreaField('Descripción')
    min_players = IntegerField('Jugadores mínimos por equipo', 
                             validators=[DataRequired(), NumberRange(min=1)])
    category = SelectField('Categoría', coerce=int)
    is_active = BooleanField('Activa')
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from flaskapp.database.models import ActivityCategory
        self.category.choices = [(c.id, c.name) for c in ActivityCategory.query.all()]