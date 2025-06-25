from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField, DateTimeField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError
from datetime import date, datetime
from flaskapp.database.models import Activity, TournamentStatus, Event, OrganizationMember
from flask_login import current_user

class TournamentForm(FlaskForm):
    name = StringField('Nombre del Torneo', validators=[DataRequired()])
    description = TextAreaField('Descripción')
    activity_id = SelectField('Actividad', coerce=int, validators=[DataRequired()])
    max_teams = IntegerField('Máximo de equipos', validators=[
        DataRequired(),
        NumberRange(min=2, message="Debe haber al menos 2 equipos")
    ])
    start_date = DateField(
        'Fecha de Inicio', 
        default=date.today, 
        validators=[DataRequired()],
        format='%Y-%m-%d'  # Asegurar formato consistente
    )
    end_date = DateField(
        'Fecha de Término', 
        default=date.today, 
        validators=[DataRequired()],
        format='%Y-%m-%d'  # Asegurar formato consistente
    )
    prizes = TextAreaField('Premios')
    status_id = SelectField('Estado', coerce=int, validators=[DataRequired()])
    event_id = SelectField('Evento (opcional)', coerce=int, validators=[Optional()])

    def __init__(self, organization_id=None, *args, **kwargs):
        super(TournamentForm, self).__init__(*args, **kwargs)
        self.organization_id = organization_id
        self._set_activity_choices()
        self._set_status_choices()
        self._set_event_choices()

    def _set_activity_choices(self):
        """Cargar actividades activas disponibles"""
        activities = Activity.query.filter_by(is_active=True).order_by(Activity.name).all()
        self.activity_id.choices = [(a.id, a.name) for a in activities]
        if not self.activity_id.choices:
            self.activity_id.choices = [(-1, "No hay actividades disponibles")]

    def _set_status_choices(self):
        """Cargar estados de torneo disponibles"""
        statuses = TournamentStatus.query.order_by(TournamentStatus.id).all()
        self.status_id.choices = [(s.id, s.code) for s in statuses]

    def _set_event_choices(self):
        """Cargar eventos disponibles para la organización"""
        if not self.organization_id:
            self.event_id.choices = [(-1, "Sin evento")]
            return
            
        events = Event.query.filter_by(organization_id=self.organization_id)\
                   .order_by(Event.start_date.desc()).all()
        self.event_id.choices = [(-1, "Sin evento")] + [(e.id, e.name) for e in events]

    def validate_max_teams(self, field):
        """Validar que el número de equipos sea potencia de 2 para torneos de eliminación"""
        if field.data and not self._is_power_of_two(field.data):
            raise ValidationError('El número de equipos debe ser una potencia de 2 (2, 4, 8, 16...) para torneos de eliminación')

    def validate_end_date(self, field):
        """Validar que la fecha final sea posterior a la fecha inicial"""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('La fecha de finalización debe ser posterior a la de inicio')

    @staticmethod
    def _is_power_of_two(n):
        """Helper method to check if a number is power of two"""
        return (n & (n-1) == 0) and n != 0