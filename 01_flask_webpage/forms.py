"""WTForms mit Eingabe-Regeln (Field Validation).

Zeigt: WTF-Forms + serverseitige Validierung. Der eingebaute CSRF-Schutz von
Flask-WTF ist hier bereits aktiv (form.hidden_tag() im Template) — das CSRF-Thema
selbst wird in Ordner 12 vertieft.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo


class RegisterForm(FlaskForm):
    username = StringField(
        "Benutzername",
        validators=[
            DataRequired(message="Pflichtfeld."),
            Length(min=3, max=32, message="3–32 Zeichen."),
            Regexp(
                r"^[A-Za-z0-9_.-]+$",
                message="Nur Buchstaben, Zahlen und _ . -",
            ),
        ],
    )
    password = PasswordField(
        "Passwort",
        validators=[
            DataRequired(),
            Length(min=8, message="Mindestens 8 Zeichen."),
        ],
    )
    confirm = PasswordField(
        "Passwort bestätigen",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwörter stimmen nicht überein."),
        ],
    )
    submit = SubmitField("Registrieren")


class LoginForm(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    submit = SubmitField("Einloggen")
