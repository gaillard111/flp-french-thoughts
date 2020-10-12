<?php

namespace ThoughtBundle\Security;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;
use ThoughtBundle\Entity\Chain;

class ChainVoter extends Voter
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

        if (!$subject instanceof Chain) {
            return false;
        }

        return true;
    }

    protected function voteOnAttribute($attribute, $subject, TokenInterface $token)
    {
        $user = $token->getUser();
        $chain = $subject;

        if (!$user instanceof User) {
            return false;
        }

        switch ($attribute) {
            case self::VIEW:
                return $this->canView($chain, $user);
            case self::EDIT:
                return $this->canEdit($chain, $user);
        }
    }

    private function canView(Chain $chain, User $user)
    {
        return true;
    }

    private function canEdit(Chain $chain, User $user)
    {
        $security = $this->service_container->get('security.authorization_checker');
        $owner = $chain->getUser();

        if (!$security->isGranted($owner, $user) and $owner !== $user) {
            return false;
        }

        return true;
    }
}