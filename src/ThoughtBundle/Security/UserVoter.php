<?php

namespace ThoughtBundle\Security;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

class UserVoter extends Voter
{
    /** @var Container */
    private $service_container;

    /**
     * @param Container $container
     */
    public function __construct(Container $container)
    {
        $this->service_container = $container;

    }

    protected function supports($attribute, $subject)
    {
        if (!$attribute instanceof User) {
            return false;
        }

        if (!$subject instanceof User) {
            return false;
        }

        return true;
    }

    protected function voteOnAttribute($attribute, $subject, TokenInterface $token)
    {
        $security = $this->service_container->get('security.authorization_checker');
        $teacher = $subject;
        $student = $attribute;

        if (!$security->isGranted('ROLE_TEACHER')) {
            return false;
        }

        if (!in_array('ROLE_STUDENT', $student->getRoles())) {
            return false;
        }

        if (!$teacher->isInTheTeacherGroup($student)) {
            return false;
        }

        return true;
    }

}