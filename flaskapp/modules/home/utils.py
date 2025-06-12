# utils.py

from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar

class TimeLabelGenerator:
    """Genera etiquetas de tiempo (meses, semanas, días) para gráficas."""

    def get_last_month_labels(self, count=6):
        """Retorna los últimos `count` meses como abreviaturas."""
        today = datetime.today()
        return [
            calendar.month_abbr[(today - relativedelta(months=i)).month]
            for i in reversed(range(count))
        ]


if __name__ == "__main__":
    # Ejemplo de uso
    generator = TimeLabelGenerator()
    labels = generator.get_last_month_labels(6)
    print(labels)  # ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']