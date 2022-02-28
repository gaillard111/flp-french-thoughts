<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\OptimisticLockException;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Entity\Thought;

trait LikeModelTrait
{

    public function addLike(Thought $thought, User $user)
    {
        $recommendedThoughtService = $this->container->get('thought.recommended_thought');

        $like = new Like();
        $like
            ->setUser($user)
            ->setThought($thought);
        $thought->addLike($like);

        $this->em->persist($thought);
        $this->em->flush();

        $recommendedThoughtService->addWatchedThought($user, $thought);

        return $thought;
    }

    public function removeLike(Thought $thought, User $user)
    {
        /** @var Like[] $likes */
        $likes = $thought->getLikes();

        foreach ($likes as $like) {
            if ($like->getUser() === $user) {
                $this->em->remove($like);
                $this->em->flush();
            }
        }

        return $thought;
    }

    public function addSessionLike(Thought $thought)
    {
        $thought->incrementLikeCount();
        $this->em->persist($thought);
        $this->em->flush();
    }

    public function removeSessionLike(Thought $thought)
    {
        $thought->reduceLikeCount();
        $this->em->persist($thought);
        $this->em->flush();
    }

    public function isLiked(Thought $thought, User $user)
    {
        if ( $this->em->getRepository(Like::class)->isUserLikeThought($user, $thought) ) {
            return true;
        }

        return false;
    }
}