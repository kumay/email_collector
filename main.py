import imaplib
import email
import base64
import quopri


def get_body_text(payload, email_encoding):

    body = None
    _type = payload.get_content_type()

    if _type == "text/plain" or _type == "text/html":

        text_encoding = payload.get_charsets()[0]
        content_transfer_encoding = payload.get("Content-Transfer-Encoding")
        # extract body
        content = payload.get_payload()

        if content_transfer_encoding == "base64" or content_transfer_encoding == "Base64":
            body = base64.urlsafe_b64decode(content)
        elif content_transfer_encoding == "7bit":
            body = content
        elif content_transfer_encoding == "quoted-printable":
            body = quopri.decodestring(content, header=False)

        if text_encoding == "iso-2022-jp":
            try:
                if type(body) == bytes:
                    body = body.decode(email_encoding, "ignore")
                else:
                    body = body.encode(email_encoding).decode(email_encoding, "ignore")
            except Exception as e:
                body = body
        else:
            if body is not None:
                try:
                    body = body.decode(email_encoding, "ignore")
                except Exception as e:
                    print(e)
            else:
                body = ""

    return _type, body


def get_messages(service_name, email_address, access_token, port, query):

    search_term = query  # "SINCE 9-Dec-2018 SEEN"

    with imaplib.IMAP4_SSL(host=service_name, port=port) as mail:

        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (email_address, access_token)

        mail.authenticate('XOAUTH2', lambda x: auth_string)
        mail.select(mailbox='INBOX', readonly=False)

        typ, mails = mail.search(None, search_term)

        for _mail in mails[0].split():
            _typ, data = mail.fetch(_mail, '(RFC822)')

            raw_mail = email.message_from_bytes(data[0][1])

            # get email encoding
            email_encoding = email.header.decode_header(raw_mail.get('Subject'))[0][1] or 'iso-2022-jp'

            # check for multipart
            is_multipart = raw_mail.is_multipart()

            if is_multipart:
                for payload in raw_mail.get_payload():
                    _type, _body = get_body_text(payload, email_encoding)

            else:
                _type, _body = get_body_text(raw_mail, email_encoding)

            print(_body)
