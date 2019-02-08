<?php

namespace ThoughtBundle\Command;

use Symfony\Bundle\FrameworkBundle\Command\ContainerAwareCommand;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use ThoughtBundle\Service\Mail;

class MailCommand extends ContainerAwareCommand
{

    public function __construct($name = null)
    {
        parent::__construct($name);
    }

    /**
     * {@inheritdoc}
     */
    protected function configure()
    {
        $this
            ->setName('throught:mail_command')
            ->setDescription('Sending email to all users')
            ->addArgument('mail', InputArgument::REQUIRED);
    }

    /**
     * {@inheritdoc}
     */
    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $mailId = $input->getArgument('mail');
        dump($mailId);
        $entityManager = $this->getContainer()->get('doctrine')->getEntityManager();

        $users = $entityManager->getRepository('ApplicationSonataUserBundle:User')->findAll();
        $mail  = $entityManager->getRepository('ThoughtBundle:GeneralMail')->find($mailId);
//        dump($mail); die;
        if ($mail) {

            /** @var Mail $serviceMail */
            $serviceMail = $this->getContainer()->get('thought.service.mail_service');
            $serviceMail->generalMail($users, $mail->getSubject(), nl2br($mail->getBody()));

            $mail->setIsSended(true);
            $entityManager->persist($mail);
            $entityManager->flush();

        } else {
            $output->writeln('Mail not found');
        }
    }
}
