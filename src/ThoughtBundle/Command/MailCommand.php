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

        $entityManager = $this->getContainer()->get('doctrine')->getEntityManager();

        $users = $entityManager->getRepository('ApplicationSonataUserBundle:User')->findAll();
        $mail  = $entityManager->getRepository('ThoughtBundle:GeneralMail')->find($mailId);

        if ($mail) {

            /** @var Mail $serviceMail */
            $serviceMail = $this->getContainer()->get('thought.service.mail_service');
            $serviceMail->generalMail($users, $mail->getSubject(), $mail->getBody());

            $mail->setIsSended(true);
            $entityManager->persist($mail);
            $entityManager->flush();

            $output->writeln('Mail = ' . $mailId);
            foreach ($users as $user)
            {
                $output->writeln('Sended message on ' . $user->getEmail());
            }
        } else {
            $output->writeln('Mail not found');
        }
    }
}
