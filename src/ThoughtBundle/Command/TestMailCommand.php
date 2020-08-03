<?php

namespace ThoughtBundle\Command;

use Symfony\Bundle\FrameworkBundle\Command\ContainerAwareCommand;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use ThoughtBundle\Service\Mail;

class TestMailCommand extends ContainerAwareCommand
{
    /**
     * {@inheritdoc}
     */
    protected function configure()
    {
        $this
            ->setName('throught:mailer_test')
            ->setDescription('Sending email to one user')
            ->addArgument('mail', InputArgument::REQUIRED);
    }

    /**
     * {@inheritdoc}
     */
    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $mail = $input->getArgument('mail');

        /** @var Mail $serviceMail */
        $serviceMail = $this->getContainer()->get('thought.service.mail_service');
        $serviceMail->sendMail('Test email from fthoughts', $mail, 'Test sending email');

    }
}