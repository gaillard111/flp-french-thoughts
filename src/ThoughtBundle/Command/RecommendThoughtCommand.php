<?php

namespace ThoughtBundle\Command;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Bundle\FrameworkBundle\Command\ContainerAwareCommand;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class RecommendThoughtCommand extends ContainerAwareCommand
{
    /**
     * {@inheritdoc}
     */
    protected function configure()
    {
        $this
            ->setName('thought:recommend')
            ->addOption('test')
        ;
    }

    /**
     * {@inheritdoc}
     */
    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $em = $this->getContainer()->get('doctrine.orm.entity_manager');
        $recommendedThoughtService = $this->getContainer()->get('thought.recommended_thought');
        $mailService = $this->getContainer()->get('thought.service.mail_service');

        if ($input->getOption('test')) {
            $users = [
                $em->getRepository(User::class)->findOneBy(['email' => 'arseny.k@zimalab.com'])
            ];
        } else {
            /** @var User $user */
            $users = $em->getRepository(User::class)->findAll();
        }


        foreach ($users as $user) {
            $recommendedThought = null;
            while ($recommendedThought == null) {
                $recommendedThought = $recommendedThoughtService->getThought($user);
                try {
                    $thA = array_shift($recommendedThought);
                    $recommendedThought = array_shift($thA);
                    $recommendedThoughtService->addWatchedThought($user, $recommendedThought);
                } catch (\Exception $e) {
                    dump($recommendedThought);
                    continue;
                }

            }

//            dump($recommendedThought->getContent()); die;
            echo $recommendedThought->getContent();

            $mailService->sendMail('L\'extrait du jour', $user->getEmail(), '<img src="http://demo-frenchthoughts.zimalab.com/logo.png"><br>#' . $recommendedThought->getId() . ' ' . $recommendedThought->getContent());

            if ($input->getOption('test')) {
                $mailService->sendMail('L\'extrait du jour', 'gaillard111@bluewin.ch', $recommendedThought->getContent());
                echo 'gaillard111@bluewin.ch';
            }

            echo $user->getEmail();
        }



//        dump($recommendedThought[0][0]->getId(), ); die;
    }
}
