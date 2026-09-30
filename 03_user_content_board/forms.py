"""WTForms. Neu gegenüber Ordner 02: PostForm fürs Board."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo


class RegisterForm(FlaskForm):
    username = StringField(
        "Benutzername",
        validators=[
            DataRequired(message="Pflichtfeld."),
            Length(min=3, max=32, message="3–32 Zeichen."),
            Regexp(r"^[A-Za-z0-9_.-]+$", message="Nur A–Z, 0–9 und _ . -"),
        ],
    )
    password = PasswordField(
        "Passwort",
        validators=[DataRequired(), Length(min=8, message="Mindestens 8 Zeichen.")],
    )
    confirm = PasswordField(
        "Passwort bestätigen",
        validators=[DataRequired(), EqualTo("password", message="Stimmt nicht überein.")],
    )
    submit = SubmitField("Registrieren")


class LoginForm(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    submit = SubmitField("Einloggen")


class PostForm(FlaskForm):
    content = TextAreaField(
        "Beitrag",
        validators=[DataRequired(), Length(min=1, max=500, message="Max. 500 Zeichen.")],
    )
    submit = SubmitField("Posten")
