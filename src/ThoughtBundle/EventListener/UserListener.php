<?php

namespace ThoughtBundle\EventListener;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\Event\LifecycleEventArgs;
use Symfony\Component\DependencyInjection\Container;

class UserListener
{
    private $container;

    public function __construct(Container $container)
    {
        $this->container = $container;
    }

    public function preUpdate(LifecycleEventArgs $event)
    {
        $entity = $event->getEntity();

        if ($entity instanceof User ) {
            $user = $entity;
            $changeSet = $event->getEntityChangeSet();
            if (
                $user->getRole() == User::ROLE_TEACHER and
                isset($changeSet['enabled']) and
                !$user->isRegistrationConfirm()
            ) {

                if (isset($changeSet['enabled'][1]) and $changeSet['enabled'][1] === true) {
                    $emailService = $this->container->get('thought.service.mail_service');
                    $emailService->teacherActivateEmail($user);
                    $user->setRegistrationConfirm(true);
                }

            }
        }

    }
}