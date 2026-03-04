from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length


class RegistroForm(FlaskForm):
    username = StringField(
        'Nome de usuário',
        validators=[DataRequired(message="O nome de usuário é obrigatório"),
                    Length(min=3, max=20, message="O nome deve ter entre 3 e 20 caracteres")]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(message="O email é obrigatório"),
                    Email(message="Email inválido"),
                    Length(max=100)]
    )
    phone = StringField(
        'Telefone',
        validators=[DataRequired(message="O telefone é obrigatório"),
                    Length(max=15, message="Telefone muito longo")]
    )
    password = PasswordField(
        'Senha',
        validators=[DataRequired(message="A senha é obrigatória"),
                    Length(min=8, max=100, message="A senha deve ter entre 8 e 100 caracteres")]
    )
    securityQuestion = SelectField(
        'Pergunta de Segurança',
        choices=[
            ('', 'Selecione uma pergunta'),
            ('1', 'Qual o nome do seu primeiro animal de estimação?'),
            ('2', 'Qual o nome da rua onde você cresceu?'),
            ('3', 'Qual era o seu apelido de infância?'),
            ('4', 'Qual o nome do seu melhor amigo de infância?'),
            ('5', 'Qual foi sua primeira escola?')
        ],
        validators=[DataRequired(message="Você deve selecionar uma pergunta de segurança")]
    )
    securityAnswer = StringField(
        'Resposta de segurança',
        validators=[DataRequired(message="A resposta de segurança é obrigatória"),
                    Length(min=3, max=100, message="A resposta deve ter entre 3 e 100 caracteres")]
    )
    submit = SubmitField('Registrar')


class LoginForm(FlaskForm):
    identifier = StringField(
        'Usuário, Email ou Telefone',
        validators=[DataRequired(message="Informe seu usuário, email ou telefone")]
    )
    password = PasswordField(
        'Senha',
        validators=[DataRequired(message="Informe sua senha"),
                    Length(min=8, max=100)]
    )
    submit = SubmitField('Entrar')
