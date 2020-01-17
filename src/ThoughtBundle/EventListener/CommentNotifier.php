<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 12.08.19
 * Time: 15:22
 */

namespace ThoughtBundle\EventListener;


use Application\Sonata\UserBundle\Entity\User;
use Doctrine\Common\Persistence\Event\LifecycleEventArgs;
use Exception;
use Symfony\Bundle\FrameworkBundle\Routing\Router;
use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\DependencyInjection\ContainerAwareInterface;
use Symfony\Component\Stopwatch\Stopwatch;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Service\Mail;
use Twig_Environment;

class CommentNotifier
{
    /**
     * @var Mail
     */
    private $mailService;

    /**
     * @var Stopwatch
     */
    private $stopwatch;

    /**
     * @var Router
     */
    private $router;

    /**
     * @var Twig_Environment
     */
    private $twig;
    /**
     * @var Container
     */
    private $serviceContainer;


    public function __construct(Mail $mailService, Stopwatch $stopwatch, Router $router, Container $serviceContainer)
    {
        $this->mailService = $mailService;
        $this->stopwatch = $stopwatch;
        $this->router = $router;
        $this->serviceContainer = $serviceContainer;
    }

    public function postPersist(LifecycleEventArgs $args)
    {
        /** @var Comment $comment */

        $comment = $args->getObject();

        if ($comment instanceof Comment) {

            $em = $args->getObjectManager();
            /** @var User|mixed $commentUser */
            $commentUser = $em->getRepository(User::class)->findOneBy([
                'email' => $comment->getEmail()
            ]);
            $thought = $comment->getThought();
            $thoughtOwner = $thought->getOwner();
            /** @var Like[]|mixed $likes */
            $likes = $thought->getLikes();
            $comments = $thought->getComments();

            foreach ($comments as $key => $comment) {

                $comments[$key] = $comment->getEmail();
            }
            $emails = array_unique($comments->toArray());
            foreach ($emails as $email) {
                if ($email != $comment->getEmail()) {
                    $body = $this->getTwig()->render('@Thought/Notifications/alsoCommentedMail.html.twig', [
                        'user'      => $commentUser,
                        'thought'   => $comment->getThought()
                    ]);

                    $this->mailService->sendMail('Les fils de la pensée Notification', $email, $body);
                }

            }


            foreach ($likes as $like) {
                if (($like->getUser() != null) && ($comment != null)) {
                    if ($like->getUser()->getEmail() != $comment->getEmail()) {

                        $body = $this->getTwig()->render('@Thought/Notifications/commentedThoughtYouLikeMail.html.twig', [
                            'user'      => $like->getUser(),
                            'thought'   => $like->getThought()
                        ]);

                        $this->mailService->sendMail('Les fils de la pensée Notification', $like->getUser()->getEmail(), $body);
                    }
                }
            }

            if ($thoughtOwner && ($thoughtOwner->getEmail() != $comment->getEmail())) {

                $body = $this->getTwig()->render('@Thought/Notifications/commentedYourThoughtMail.html.twig', [
                    'user'      => $commentUser,
                    'thought'   => $comment->getThought()
                ]);

                $this->mailService->sendMail('Les fils de la pensée Notification', $thoughtOwner->getEmail(), $body);
            }
        }
    }

    /**
     * @return Twig_Environment
     * @throws Exception
     */
    private function getTwig()
    {
        if (!$this->twig) {
            $this->twig = $this->serviceContainer->get('twig');
        }
        return $this->twig;
    }
}