<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 13.08.19
 * Time: 15:12
 */

namespace ThoughtBundle\EventListener;


use Doctrine\Common\Persistence\Event\LifecycleEventArgs;
use Symfony\Bundle\FrameworkBundle\Routing\Router;
use Symfony\Component\Routing\Generator\UrlGeneratorInterface;
use Symfony\Component\Routing\RouterInterface;
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
        $this->router = $router;
    }

    public function postPersist(LifecycleEventArgs $args)
    {
        /** @var Like $like */
        $like = $args->getObject();
        if ($like instanceof Like) {
            $owner = $like->getThought()->getOwner();
            if (($owner != null) && ($owner != $like->getUser())) {
                $this->mailService->sendMail('Les fils de la pensée Notification', $owner->getEmail(), 'User <a href="'. $this->router->generate('thought_profile', ['userId' => $like->getUser()->getId()], Router::ABSOLUTE_URL) .'">' . $like->getUser()->getFirstname() . '</a> liked thought <a href="'. $this->router->generate('thought_thoughtpage_index', ['thoughtId' => $like->getThought()->getId()], Router::ABSOLUTE_URL) .'">' . $like->getThought()->getCategory() . '</a>');

            }
        }

    }
}