<?php

namespace ThoughtBundle\Security;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

class ProfileVoter extends Voter
{
    const VIEW = 'view';
    const EDIT = 'edit';

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
        if (!in_array($attribute, [self::VIEW, self::EDIT])) {
            return false;
        }

        if (!$subject instanceof User) {
            return false;
        }

        return true;
    }

    protected function voteOnAttribute($attribute, $subject, TokenInterface $token)
    {
        $requestedUser = $subject;
        $user = $token->getUser();

        if (!$user instanceof User) {
            return false;
        }

        switch ($attribute) {
            case self::VIEW:
                return $this->canView($user, $requestedUser);
        }

        return false;
    }

    private function canView(User $user, User $requestedUser) {
        $security = $this->service_container->get('security.authorization_checker');

        if ($user === $requestedUser) {
            return true;
        }

        if ((
                $security->isGranted('ROLE_STUDENT') ||
                $security->isGranted('ROLE_TEACHER')
            )
            ===
            (
                in_array('ROLE_STUDENT', $requestedUser->getRoles()) ||
                in_array('ROLE_TEACHER', $requestedUser->getRoles())
            )){
                return true;
                }


        return false;
    }
}