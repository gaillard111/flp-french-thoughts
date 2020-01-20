<?php

namespace ThoughtBundle\Service;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\DependencyInjection\Container;
use ThoughtBundle\Entity\Chain;
use ThoughtBundle\Entity\ChainComment;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\Thought;

/**
 * Class Mail
 *
 * @package ThoughtBundle\Service
 */
class Mail
{
    /**
     * @var Container
     */
    private $container;

    /**
     * @var \Symfony\Component\Translation\DataCollectorTranslator
     */
    private $translator;

    /**
     * Mail constructor.
     *
     * @param Container $container
     *
     * @throws \Exception
     */
    public function __construct(Container $container)
    {
        $this->container = $container;

        $this->translator = $container->get('translator');
    }

    /**
     * @param Thought $thought
     *
     * @throws \Exception
     */
    public function mailAddNewThought(Thought $thought)
    {
        $subject = 'French thought: add new thought';
        $link    = $this->container->get('router')->generate('thought_thoughtpage_index', ['thoughtId' => $thought->getId()], 0);

        $body = 'User: ' . $thought->getOwner()->getFullname() . ' in ' . $thought->getCreatedAt()->format('Y-m-d H:i') .
            ' leave thought: ' . $thought->getContent() . '<br>' .
            'To view the review click on the ' . '<a href="' . $link . '">link</a>'
        ;

        $emailUsers = $this->container->getParameter('admin_email');

        //dump($subject, $emailUsers, $body); die;
        $this->sendMail($subject, $emailUsers, $body);
    }

    /**
     * Send email - Add new comment
     *
     * @param Comment $comment
     *
     * @throws \Exception
     */
    public function mailAddNewComment(Comment $comment)
    {
        $subject = 'French thought: add new comment';

        $link = $this->container->get('router')->generate('thought_thoughtpage_index', ['thoughtId' => $comment->getThought()->getId()], 0);

        $body = 'User: ' . $comment->getFullName() . ' in ' . $comment->getCreatedAt()->format('Y-m-d H:i') .
            ' leave comment: ' . $comment->getText() . '<br>' .
            'To view the review click on the ' . '<a href="' . $link . '">link</a>'
        ;

        $emailUsers = $this->container->getParameter('admin_email');

        $this->sendMail($subject, $emailUsers, $body);
    }

    /**
     * Send email - Add new chain comment
     *
     * @param ChainComment $comment
     *
     * @throws \Exception
     */
    public function mailAddNewChainComment(ChainComment $comment)
    {
        $subject = 'French thought: add new comment to chain - ' . $comment->getChain()->getName();

        $link = $this->container->get('router')->generate('chain_page', ['chainId' => $comment->getChain()->getId()], 0);

        $body = 'User: ' . $comment->getUser()->getFullNameEmail() . ' in ' . $comment->getCreatedAt()->format('Y-m-d H:i') .
            ' leave comment: ' . $comment->getText() . '<br>' .
            'To view the review click on the ' . '<a href="' . $link . '">link</a>'
        ;

        $emails    = [$this->container->getParameter('admin_email')];
        $emailUser = ($comment->getUser()->getId() != $comment->getChain()->getUser()->getId()) ? $comment->getChain()->getUser()->getEmail() : null;

        if ($emailUser) {
            array_push($emails, $emailUser);
        }

        $this->sendMail($subject, $emails, $body);
    }

    /**
     * @param $users
     *
     * @throws \Exception
     */
    public function generalMail($users, $subject, $body)
    {
        /**
         * @var User $user
         */
        foreach ($users as $key => $user) {
            if (filter_var($user->getEmail(), FILTER_VALIDATE_EMAIL)) {
                $this->sendMail($subject, $user->getEmail(), $body);
            }
        }
    }

    /**
     * @param User  $user
     * @param Chain $chain
     *
     * @throws \Twig_Error
     */
    public function notificationMail(User $user, User $curUser, Chain $chain, Thought $thought)
    {
        $userEmail = $user->getEmail();
        $subject   = 'You have a new quote in your chain';
        $body      = $this->container->get('templating')->render('@ApplicationSonataUser/Mail/chainNotification.html.twig', [
                'chain'   => $chain,
                'thought' => $thought,
                'curUser' => $curUser,
            ]);
        $this->sendMail($subject, $userEmail, $body);
    }

    /**
     * @param User $user
     * @param $requestId
     *
     * @throws \Twig_Error
     */
    public function friendNotificationMail(User $user, User $friend, $requestId)
    {
        $friendEmail = $friend->getEmail();
        $subject     = 'User ' . $user->getFirstname() . ' ' . $user->getLastname() . ' has sent you friend request';
        $body        = $this->container->get('templating')->render('@ApplicationSonataUser/Mail/friendNotification.html.twig', [
                'user'  => $user,
                'reqId' => $requestId,
            ]);
        $this->sendMail($subject, $friendEmail, $body);
    }

    /**
     * @param $subject
     * @param $emailUsers
     * @param $body
     * @param null $cc
     *
     * @throws \Exception
     */
    public function sendMail($subject, $emailUser, $body, $cc = null)
    {
        $message = \Swift_Message::newInstance()
            ->setSubject($subject)
            ->setFrom($this->container->getParameter('mailer_user'))
            ->setTo($emailUser)
            ->setBody($body, 'text/html')
        ;

        if ($cc) {
            $message->setCc($cc);
        }

        $mailer = $this->container->get('mailer');

        try {
            $mailer->send($message);
//            sleep(10);
        } catch (\Swift_TransportException $exception) {
            $mailer->getTransport()->stop();
//            sleep(20);
            $mailer->send($message);
        }
    }
}
