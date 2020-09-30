<?php


namespace ThoughtBundle\EventListener;

use Doctrine\ORM\EntityManager;
use FOS\UserBundle\Event\FormEvent;
use FOS\UserBundle\FOSUserEvents;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

class RegistrationListener implements EventSubscriberInterface
{
    /**
     * @var EntityManager
     */
    private $em;

    /**
     * @param \Doctrine\ORM\EntityManager $entityManager
     */
    public function __construct(EntityManager $entityManager)
    {
        $this->em = $entityManager;
    }

    public static function getSubscribedEvents()
    {
        return array(
            FOSUserEvents::REGISTRATION_SUCCESS     => 'onRegistrationSuccess',
        );
    }

    /**
     * @param FormEvent $event
     */
    public function onRegistrationSuccess(FormEvent $event)
    {
        $user = $event->getForm()->getData();
        $formData = $event->getRequest()->request->get('fos_user_registration_form');

        if ($formData['roles'] == 'student') {
            $user->setRoles(['ROLE_STUDENT']);
        }

        if ($formData['roles'] == 'teacher') {
            $user->setRoles(['ROLE_TEACHER']);
        }
    }

}