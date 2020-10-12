<?php

namespace ThoughtBundle\Controller;

use Application\Sonata\UserBundle\Entity\Message;
use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\NonUniqueResultException;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RequestStack;
use Symfony\Component\HttpFoundation\Response;
use ThoughtBundle\Entity\MenuItem;
use ThoughtBundle\Entity\Topic;

class RenderController extends Controller
{
    public function navbarAction()
    {
        $roots = $this->getDoctrine()->getRepository(MenuItem::class)->findBy(['level' => 0], ['sort' => 'ASC']);

        $virtualRoot = new MenuItem();
        $virtualRoot->setChildren($roots);

        return $this->render('@Thought/navigate.html.twig', [
            'root' => $virtualRoot,
        ]);
    }

    /**
     * @param $routeName
     * @return Response
     * @throws NonUniqueResultException
     * @throws \Doctrine\ORM\Query\QueryException
     */
    public function menuAction($routeName, $mobile = false)
    {
        $menuService = $this->get('thought.menu');
        $menu        = $menuService->makeMenu($this->getUser());

        /** @var User $user */
        $user = $this->getUser();

        $thoughts = $this->container
            ->get('thought.model.thought_model')->getCountUserThoughts($this->getUser());

        /** @var RequestStack $requestStack */
        $requestStack = $this->get('request_stack');

        $count       = $this->getDoctrine()->getRepository(Message::class)->getCountNewMessages($user);
        $countTopics = $this->getDoctrine()->getRepository(Topic::class)->getCountUserTopics($user);
        if (!$mobile) {
            return $this->render('@Thought/Profile/menu.html.twig', [
                'menu'             => $menu,
                'routeName'        => $routeName,
                'thoughts'         => $thoughts,
                'newMessagesCount' => $count,
                'countTopics'      => $countTopics,
                'userProfileId'    => $requestStack->getMasterRequest()->get('userId'),
            ]);
        } else {
            return $this->render('@Thought/Profile/mobile_menu.html.twig', [
                'menu'             => $menu,
                'routeName'        => $routeName,
                'thoughts'         => $thoughts,
                'newMessagesCount' => $count,
                'countTopics'      => $countTopics,
                'userProfileId'    => $requestStack->getMasterRequest()->get('userId'),
            ]);
        }
    }
}