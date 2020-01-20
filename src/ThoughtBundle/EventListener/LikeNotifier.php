<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 13.08.19
 * Time: 15:12
 */

namespace ThoughtBundle\EventListener;

use Doctrine\Common\Persistence\Event\LifecycleEventArgs;
use Exception;
use Symfony\Bundle\FrameworkBundle\Routing\Router;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Service\Mail;

class LikeNotifier
{
    /**
     * @var Mail
     */
    private $mailService;

    /**
     * @var Router
     */
    private $router;

    public function __construct(Mail $mailService, Router $router)
    {
        $this->mailService = $mailService;
        $this->router      = $router;
    }

    /**
     * @param LifecycleEventArgs $args
     *
     * @throws Exception
     */
    public function postPersist(LifecycleEventArgs $args)
    {
        /** @var Like $like */
        $like = $args->getObject();
        if ($like instanceof Like) {
            $owner = $like->getThought()->getOwner();
            if (($owner != null) && ($owner != $like->getUser())) {
                $subject = 'Les fils de la pensée Notification';
                $body    = $this->getMailBody($like);

                $this->mailService->sendMail($subject, $owner->getEmail(), $body);
            }
        }
    }

    private function getMailBody(Like $like)
    {
        $profileRoute = $this->router->generate(
            'thought_profile',
            ['userId' => $like->getUser()->getId()],
            Router::ABSOLUTE_URL
        );
        $homepageRoute = $this->router->generate(
            'thought_thoughtpage_index',
            ['thoughtId' => $like->getThought()->getId()],
            Router::ABSOLUTE_URL
        );
        $userFirstname = $like->getUser()->getFirstname();
        $thoughtTitle  = $like->getThought()->getCategory();

        return 'User <a href="' . $profileRoute . '">' . $userFirstname . '</a> likes the <a href="' . $homepageRoute . '">' . $thoughtTitle . '</a> quote added by you.';
    }
}