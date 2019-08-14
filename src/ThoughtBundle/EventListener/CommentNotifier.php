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
use Symfony\Bundle\FrameworkBundle\Routing\Router;
use Symfony\Component\Stopwatch\Stopwatch;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Service\Mail;

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


    public function __construct(Mail $mailService, Stopwatch $stopwatch, Router $router)
    {
        $this->mailService = $mailService;
        $this->stopwatch = $stopwatch;
        $this->router = $router;
    }

    public function postPersist(LifecycleEventArgs $args)
    {
        /** @var Comment|mixed $comment */

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

//        $this->stopwatch->start('mailing');

            foreach ($comments as $key => $comment) {

                $comments[$key] = $comment->getEmail();
            }
            $emails = array_unique($comments->toArray());

            foreach ($emails as $email) {
//            dump(1, $email, $comment->getEmail());
                if ($email != $comment->getEmail()) {
                    $this->mailService->sendMail('Les fils de la pensée Notification', $email, 'User <a href="' . $this->router->generate('thought_profile', ['userId' => $commentUser->getId()], Router::ABSOLUTE_URL) . '">' . $comment->getFullName() . '</a> also commented this <a href="' .  $this->router->generate('thought_thoughtpage_index', ['thoughtId' => $comment->getThought()->getId()], Router::ABSOLUTE_URL) . '">thought</a> ');
                }

            }


            foreach ($likes as $like) {
//                dump($comment); die;
//            dump(2, $like->getUser()->getEmail(), $comment->getEmail());
                if ($like->getUser()->getEmail() != $comment->getEmail()) {
                    $this->mailService->sendMail('Les fils de la pensée Notification', $like->getUser()->getEmail(), 'The <a href="' . $this->router->generate('thought_thoughtpage_index', ['thoughtId' => $like->getThought()->getId()], Router::ABSOLUTE_URL) . '">thought</a> you like also liked <a href="' . $this->router->generate('thought_profile', ['userId' => $commentUser->getId()], Router::ABSOLUTE_URL) . '">' . $comment->getFullName() . '</a>');
                }


            }

//        dump(3, $thoughtOwner->getEmail(), $comment->getEmail());

            if ($thoughtOwner->getEmail() != $comment->getEmail()) {
                $this->mailService->sendMail('Les fils de la pensée Notification', $thoughtOwner->getEmail(), '<a href="' . $this->router->generate('thought_profile', ['userId' => $commentUser->getId()],  Router::ABSOLUTE_URL) . '">' . $comment->getFullName() . '</a> commented your <a href="' . $this->router->generate('thought_thoughtpage_index', ['thoughtId' => $comment->getThought()->getId()], Router::ABSOLUTE_URL) . '">thought</a>');
            }
        }
    }
}