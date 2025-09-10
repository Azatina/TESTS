import asyncio
from aiosmtpd.controller import Controller


class ExampleHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        if address.endswith('@example111.com') or address.endswith('@ggg111.com'):
            print(f'450 4.1.2 {address}: Recipient address rejected: Domain not found')
            return f'450 4.1.2 {address}: Recipient address rejected: Domain not found'
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        print('Message from %s' % envelope.mail_from)
        print('Message for %s' % envelope.rcpt_tos)
        print('Message data:\n')
        for ln in envelope.content.decode('utf8', errors='replace').splitlines():
            print(f'> {ln}'.strip())
        print()
        print('End of message')
        return '250 Message accepted for delivery'


controller = Controller(ExampleHandler(), hostname='192.168.0.121', port=8025)
controller.start()
input("Server started. Press Return to quit.")
controller.stop()
