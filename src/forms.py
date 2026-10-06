# Flask Forms
from flask_wtf import FlaskForm
from wtforms import StringField, Field, HiddenField, TextAreaField
from wtforms.validators import (DataRequired, 
                                EqualTo, Optional, 
                                Regexp, ValidationError)
from wtforms.widgets import TextInput, html_params
from markupsafe import Markup
from .database import guestbook_by_name

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

def name_not_taken(form: FlaskForm, field: StringField):
    '''Ensure the username has not been registered'''
    if not field.data: 
        raise ValidationError(f"Please supply a username!")
    if guestbook_by_name(field.data):
        raise ValidationError(f"'{field.data}' is already taken!")

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
class GuestBookForm(FlaskForm):
    # Disallow logged in users
    username    =   HiddenField(validators=[Optional(), EqualTo('name')])
    name        =   StringField("Your Name",
                            validators=[
                                DataRequired('A Username is Required!'),
                                Regexp(
                                    "^[A-Za-z][A-Za-z0-9_.]*$", 
                                    0,
                                    "Usernames must have only letters, " "numbers, dots or underscores",
                                    ),
                                name_not_taken
                                ]
                            )
    message     =   TextAreaField("Leave a Message", validators=[Optional()])
    submit      =   SubmitButtonField("Sign")
