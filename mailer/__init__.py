VERSION = (0, 2, 0, "a", 1) # following PEP 386
DEV_N = None


def get_version():
    version = "%s.%s" % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = "%s.%s" % (version, VERSION[2])
    if VERSION[3] != "f":
        version = "%s%s%s" % (version, VERSION[3], VERSION[4])
        if DEV_N:
            version = "%s.dev%s" % (version, DEV_N)
    return version


__version__ = get_version()


PRIORITY_MAPPING = {
    "high": "1",
    "medium": "2",
    "low": "3",
    "deferred": "4",
}


# replacement for django.core.mail.send_mail


def send_mail(subject, message, from_email, recipient_list, priority="medium",
              fail_silently=False, auth_user=None, auth_password=None):
    from django.utils.encoding import force_unicode
    from mailer.models import make_message
    
    priority = PRIORITY_MAPPING[priority]
    
    # need to do this in case subject used lazy version of ugettext
    subject = force_unicode(subject)
    message = force_unicode(message)
    
    message = make_message(subject=subject,
                           body=message,
                           from_email=from_email,
                           to=recipient_list,
                           priority=priority)
    if priority == "high":
        send_now(message)
    else:
        message.save()
    return 1


def send_html_mail(subject, message, message_html, from_email, recipient_list,
                   priority="medium", fail_silently=False, auth_user=None,
                   auth_password=None):
    """
    Function to queue HTML e-mails
    """
    from django.utils.encoding import force_unicode
    from django.core.mail import EmailMultiAlternatives
    from mailer.models import make_message
    
    priority = PRIORITY_MAPPING[priority]
    
    # need to do this in case subject used lazy version of ugettext
    subject = force_unicode(subject)
    message = force_unicode(message)
    
    msg = make_message(subject=subject,
                       body=message,
                       from_email=from_email,
                       to=recipient_list,
                       priority=priority)
    email = msg.email
    email = EmailMultiAlternatives(email.subject, email.body, email.from_email, email.to)
    email.attach_alternative(message_html, "text/html")
    msg.email = email
    if priority == "high":
        send_now(msg)
    else:
        msg.save()
    return 1


def send_mass_mail(datatuple, fail_silently=False, auth_user=None,
                   auth_password=None, connection=None):
    from mailer.models import make_message
    num_sent = 0
    for subject, message, sender, recipient in datatuple:
        num_sent += send_mail(subject, message, sender, recipient)
    return num_sent


def mail_admins(subject, message, fail_silently=False, connection=None, priority="medium"):
    from django.conf import settings
    from django.utils.encoding import force_unicode
    
    return send_mail(settings.EMAIL_SUBJECT_PREFIX + force_unicode(subject),
                     message,
                     settings.SERVER_EMAIL,
                     [a[1] for a in settings.ADMINS])


def mail_managers(subject, message, fail_silently=False, connection=None, priority="medium"):
    from django.conf import settings
    from django.utils.encoding import force_unicode
    
    return send_mail(settings.EMAIL_SUBJECT_PREFIX + force_unicode(subject),
                     message,
                     settings.SERVER_EMAIL,
                     [a[1] for a in settings.MANAGERS])

def send_now(message):
    connection = get_connection(backend=EMAIL_BACKEND)
    logging.info("sending message now '%s' to %s" % (message.subject.encode("utf-8"), u", ".join(message.to_addresses).encode("utf-8")))
    email = message.email
    email.connection = connection
    email.send()
    MessageLog.objects.log(message, 1) # @@@ avoid using literal result code
