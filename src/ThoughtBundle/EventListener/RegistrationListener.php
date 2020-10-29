<?php


namespace ThoughtBundle\EventListener;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use FOS\UserBundle\Event\FilterUserResponseEvent;
use FOS\UserBundle\Event\FormEvent;
use FOS\UserBundle\FOSUserEvents;
use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

class RegistrationListener implements EventSubscriberInterface
{
    /**
     * @var EntityManager
     */
    private $em;

    /** @var Container */
    private $container;

    /**
     * @param \Doctrine\ORM\EntityManager $entityManager
     * @param Container $container
     */
    public function __construct(EntityManager $entityManager, Container $container)
    {
        $this->em = $entityManager;
        $this->container = $container;
    }

    public static function getSubscribedEvents()
    {
        return array(
            FOSUserEvents::REGISTRATION_SUCCESS     => 'onRegistrationSuccess',
            FOSUserEvents::REGISTRATION_COMPLETED   => 'onRegistrationCompleted'
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
            $user->setEnabled(false);

        }
    }

    public function onRegistrationCompleted(FilterUserResponseEvent $event) {
        $user = $event->getUser();
        if ($user->getRole() == User::ROLE_TEACHER) {
            $emailService = $this->container->get('thought.service.mail_service');
            $emailService->newTeacherMail($user);
        }

    }

}