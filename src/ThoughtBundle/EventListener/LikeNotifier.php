<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 13.08.19
 * Time: 15:12
 */

namespace ThoughtBundle\EventListener;


use Doctrine\Common\Persistence\Event\LifecycleEventArgs;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Service\Mail;

class LikeNotifier
{
    /**
     * @var Mail
     */
    private $mailService;

    public function __construct(Mail $mailService)
    {
        $this->mailService = $mailService;
    }

    public function postPersist(LifecycleEventArgs $args)
    {
        /** @var Like $like */
        $like = $args->getObject();
        if ($like instanceof Like) {
            $owner = $like->getThought()->getOwner();
            if (($owner != null) && ($owner != $like->getUser())) {
                $this->mailService->sendMail('Les fils de la pensée Notification', $owner->getEmail(), 'User ' . $like->getUser()->getFirstname() . ' liked thought ' . $like->getThought()->getCategory());
            }
        }

    }
}