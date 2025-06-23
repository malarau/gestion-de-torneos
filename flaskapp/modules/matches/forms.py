from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange, Optional

class MatchResultForm(FlaskForm):
    score_team_a = IntegerField(
        'Puntuación Equipo A',
        validators=[
            DataRequired(message="La puntuación es requerida"),
            NumberRange(min=0, message="La puntuación no puede ser negativa")
        ]
    )
    
    score_team_b = IntegerField(
        'Puntuación Equipo B',
        validators=[
            DataRequired(message="La puntuación es requerida"),
            NumberRange(min=0, message="La puntuación no puede ser negativa")
        ]
    )
    
    best_player_id = SelectField(
        'Jugador Destacado',
        coerce=int,
        validators=[Optional()]
    )