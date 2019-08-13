<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 12.08.19
 * Time: 15:22
 */

namespace ThoughtBundle\EventListener;


use Doctrine\Common\Persistence\Event\LifecycleEventArgs;
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

    public function __construct(Mail $mailService, Stopwatch $stopwatch)
    {
        $this->mailService = $mailService;
        $this->stopwatch = $stopwatch;
    }

    public function postPersist(LifecycleEventArgs $args)
    {
        /** @var Comment|mixed $comment */
        $comment = $args->getObject();
        if ($comment instanceof Comment) {
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
                    $this->mailService->sendMail('Les fils de la pensée Notification', $email, 'User ' . $comment->getFullName() . ' also commented this thought');
                }

            }


            foreach ($likes as $like) {
//                dump($comment); die;
//            dump(2, $like->getUser()->getEmail(), $comment->getEmail());
                if ($like->getUser()->getEmail() != $comment->getEmail()) {
                    $this->mailService->sendMail('Les fils de la pensée Notification', $like->getUser()->getEmail(), 'The thought you like also liked ' . $comment->getFullName());
                }


            }

//        dump(3, $thoughtOwner->getEmail(), $comment->getEmail());

            if ($thoughtOwner->getEmail() != $comment->getEmail()) {
                $this->mailService->sendMail('Les fils de la pensée Notification', $thoughtOwner->getEmail(), $comment->getFullName() . ' commented your thought');
            }
        }
    }
}