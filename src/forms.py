'''Flask Forms Setup'''

from flask_wtf import FlaskForm
from wtforms import (StringField, Field, HiddenField, TextAreaField,
                      BooleanField, SelectField, PasswordField, ValidationError)
from wtforms.validators import (DataRequired, InputRequired,
                                EqualTo, Optional, IPAddress,
                                 MacAddress, Regexp)
from wtforms.widgets import TextInput, html_params
from markupsafe import Markup
from .database import guestbook_by_name, guestbook_by_id

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

# --- Custom Widgets --- #
class ButtonWidget(object):
    '''A custom widget that will display a button for submitting a form, instead of an input.  
    Source:
        - https://stackoverflow.com/questions/14510630/wtforms-creating-a-custom-widget'''
    html_params = staticmethod(html_params)
    validation_attrs = ["required", "disabled"]

    def __init__(self, input_type='submit', **kwargs):
        self.input_type = input_type

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        kwargs.setdefault("value", field.label.text)
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        # innerhtml = field._value()
        input_params = self.html_params(name=field.name, **kwargs)
        return Markup(f"<button {input_params}><span>{field.label.text}</span></button>")
    
# --- Custom Validators --- #
def name_not_taken(form: FlaskForm, field: StringField):
    '''Ensure the username has not been registered'''
    if not field.data: 
        raise ValidationError(f"A Username is Required!")
    if guestbook_by_name(field.data):
        raise ValidationError(f"The name '{field.data}' is already taken!")


def guestbook_exists(form: FlaskForm, field: StringField):
    '''Ensure the guestbook exists at the given ID'''
    if not field.data: 
        raise ValidationError("No ID provided!")
    try:
        if not guestbook_by_id(int(field.data)):
            raise ValidationError(f"No Guestbook matching '{field.data}' found!")
    except ValueError:
        raise ValidationError(f"ID '{field.data}' not valid!")


class OptionalIf(Optional):
    '''a validator which makes a field optional if another field has any truthy value.  
    Source:
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
    '''
    def __init__(self, other_field_name: str, *args, **kwargs): # message: str|None = None,
        self.other_field_name = other_field_name
        super(OptionalIf, self).__init__(*args, **kwargs)

    def __call__(self, form: FlaskForm, field: Field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception(f'No field named "{self.other_field_name}" in form "{form}".')
        if bool(other_field.data):
            super(OptionalIf, self).__call__(form, field)


class RequiredIf(InputRequired):
    '''a validator which makes a field InputRequired if another field is input with any truthy value.  
    Source:
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
    '''
    def __init__(self, other_field_name: str, message: str|None=None, *args, **kwargs):
        self.other_field_name = other_field_name
        self.message = message
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form: FlaskForm, field: Field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception(f'No field named "{self.other_field_name}" in form "{form}".')
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)


# --- Custom Fields --- #
class SubmitButtonField(Field):
    '''Represents an HTML form submit button instead of an input field.'''
    widget = ButtonWidget()

    def __init__(self, label: str | None = None, validators = None, **kwargs):
        super().__init__(label, validators, **kwargs)

    def _value(self):
        if self.data:
            return u''.join(self.data)
        return u''


# --- GUESTBOOK --- #
class GuestbookForm(FlaskForm):
    name        =   StringField("Your Name",
                            validators=[
                                name_not_taken,
                                InputRequired('A Username is Required!'),
                                Regexp(
                                    regex="^(?=.{5,32}$)[a-zA-Z0-9._~]*$", 
                                    flags=0,
                                    message="Usernames must be at least 5 characters and have only letters, numbers, dots or underscores",
                                    )
                                ]
                            )
    message     =   TextAreaField("Leave a Message", validators=[Optional()])
    confirm     =   BooleanField("I have agreed to the Terms of Service",
                                 validators=[
                                     InputRequired("You must agree to the Terms of Service"),
                                    ])
    submit      =   SubmitButtonField("Sign")

# ADMIN
class LoginForm(FlaskForm):
    username    =   StringField("Username",     validators=[InputRequired()])
    password    =   PasswordField("Password",   validators=[InputRequired()])
    rememberme  =   BooleanField("Remember Me")
    submit      =   SubmitButtonField("Login")


class AdminRemoveForm(FlaskForm):
    id          =   StringField("Entry ID",
        validators=[
            DataRequired("No ID provided!"),
            Regexp(
                regex="^[0-9]*$",
                message=f"ID not valid!"
            ),
            guestbook_exists
        ]
    )
    submit      =   SubmitButtonField("Remove")


class AdminBanForm(FlaskForm):
    ip          =   StringField("IP Address",
        validators=[
            IPAddress(message="Not a valid IP address!"),
            InputRequired('No IP entered!')
            # OptionalIf('mac')

        ]
    )
    # mac          =   StringField("MAC Address",
    #     validators=[
    #         MacAddress(message="Not a valid MAC address!"),
    #         OptionalIf('ip')

    #     ]
    # )
    submit      =   SubmitButtonField("Ban")


class AdminUnbanForm(FlaskForm):
    ip          =   StringField("IP Address",
        validators=[
            IPAddress(message="Not a valid IP address!"),
            InputRequired('No IP entered!')

        ]
    )
    submit      =   SubmitButtonField("Unban")